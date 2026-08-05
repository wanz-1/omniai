"""Stateful in-memory fake AsyncSession for E2E workflow tests.

The real codebase depends on PostgreSQL (JSONB, UUID) so an in-memory SQLite DB is
not viable here. Instead this fake stores ORM objects in memory and answers the
``execute(select(...))`` / ``get(Model, id)`` / ``add`` / ``flush`` / ``delete``
calls that the API handlers make, so genuine multi-step flows (register -> login ->
refresh -> logout) can be exercised end-to-end and their DB state asserted.
"""
import uuid
from collections import defaultdict
from datetime import datetime, timezone

from sqlalchemy.sql import operators
from sqlalchemy.sql.dml import Delete, Update
from sqlalchemy.sql.elements import BinaryExpression, BindParameter, BooleanClauseList, Grouping
from sqlalchemy.sql.functions import FunctionElement

from conftest import populate_defaults

_COMPARE_OPS = {operators.le: "le", operators.lt: "lt", operators.ge: "ge", operators.gt: "gt"}


def _unwrap_param(value):
    if isinstance(value, BindParameter):
        return value.value
    if isinstance(value, list):
        return [_unwrap_param(v) for v in value]
    return value


def _extract_predicates(whereclause):
    preds = {}

    def walk(node, target):
        if node is None:
            return
        if isinstance(node, BooleanClauseList):
            op = getattr(node, "operator", None)
            if op is operators.or_:
                alternatives = []
                for child in node.get_children():
                    sub = {}
                    walk(child, sub)
                    if sub:
                        alternatives.append(sub)
                if alternatives:
                    target["__or__"] = alternatives
                return
            for child in node.get_children():
                walk(child, target)
        elif isinstance(node, Grouping):
            walk(getattr(node, "element", None), target)
        elif isinstance(node, BinaryExpression):
            key = getattr(node.left, "key", None)
            if not key:
                return
            op = node.operator
            if op is operators.eq:
                target[key] = _unwrap_param(node.right)
            elif op is operators.in_op:
                target[key] = ("in", _unwrap_param(node.right))
            elif op in _COMPARE_OPS:
                target[key] = (_COMPARE_OPS[op], _unwrap_param(node.right))
            elif op is operators.ilike_op:
                target[key] = ("ilike", _unwrap_param(node.right))

    walk(whereclause, preds)
    return preds


def _eq(a, b):
    if isinstance(a, uuid.UUID) and isinstance(b, str):
        return str(a) == b
    if isinstance(b, uuid.UUID) and isinstance(a, str):
        return a == str(b)
    return a == b


def _obj_matches(obj, preds):
    for k, v in preds.items():
        if k == "__or__":
            if not any(_obj_matches(obj, alt) for alt in v):
                return False
            continue
        # Predicates may reference join-partner tables; objects lacking the
        # column are not constrained by that predicate.
        if not hasattr(obj, k):
            continue
        actual = getattr(obj, k)
        if isinstance(v, tuple) and v:
            tag = v[0]
            if tag == "in":
                if not any(_eq(actual, val) for val in v[1]):
                    return False
            elif tag == "ilike":
                pattern = str(v[1]).replace("%", "").lower()
                if pattern and pattern not in str(actual).lower():
                    return False
            else:
                val = v[1]
                try:
                    ok = {"le": actual <= val, "lt": actual < val,
                          "ge": actual >= val, "gt": actual > val}[tag]
                except TypeError:
                    ok = False
                if not ok:
                    return False
        elif not _eq(actual, v):
            return False
    return True


def _unwrap_row(row):
    """Column-only selects yield 1-tuples; scalar accessors return the value."""
    if isinstance(row, tuple) and len(row) == 1:
        return row[0]
    return row


class FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def scalar_one_or_none(self):
        if not self._rows:
            return None
        return _unwrap_row(self._rows[0])

    def scalar(self):
        if not self._rows:
            return None
        return _unwrap_row(self._rows[0])

    def first(self):
        if not self._rows:
            return None
        return _unwrap_row(self._rows[0])

    def one(self):
        if len(self._rows) != 1:
            raise ValueError("Expected exactly one row")
        return self._rows[0]

    def unique(self):
        return self

    def scalars(self):
        return FakeScalars([_unwrap_row(r) for r in self._rows])

    def all(self):
        return list(self._rows)

    def yield_per(self, _=None):
        return iter(self._rows)


class FakeScalars:
    def __init__(self, rows):
        self._rows = rows

    def __iter__(self):
        return iter(self._rows)

    def all(self):
        return list(self._rows)

    def first(self):
        return self._rows[0] if self._rows else None


def _value_of(node):
    if isinstance(node, BinaryExpression):
        return _value_of(node.right)
    return getattr(node, "value", node)


class FakeSession:
    """Replicates the subset of AsyncSession used by API handlers."""

    def __init__(self):
        self._store = defaultdict(dict)  # model class -> {id: obj}
        self._removed = defaultdict(dict)

    # ── introspection helpers for tests ────────────────────────────────
    def objects_of(self, model):
        return list(self._store[model].values())

    def find(self, model, **attrs):
        for obj in self._store[model].values():
            if all(getattr(obj, k, None) == v for k, v in attrs.items()):
                return obj
        return None

    # ── AsyncSession API ───────────────────────────────────────────────
    def add(self, obj):
        populate_defaults(obj)
        if getattr(obj, "id", None) is None:
            obj.id = uuid.uuid4()
        if getattr(obj, "created_at", None) is None:
            obj.created_at = datetime.now(timezone.utc)
        if getattr(obj, "updated_at", None) is None:
            obj.updated_at = datetime.now(timezone.utc)
        self._store[type(obj)][obj.id] = obj
        self._removed[type(obj)].pop(obj.id, None)

    def add_all(self, objs):
        for o in objs:
            self.add(o)

    async def execute(self, stmt, *_args, **_kwargs):
        # delete(Model).where(...): remove matching rows from the store.
        if isinstance(stmt, Delete):
            table_key = getattr(getattr(stmt, "table", None), "key", None)
            cls = next((c for c in self._store
                        if table_key and getattr(c, "__table__", None) is not None
                        and c.__table__.key == table_key), None)
            preds = _extract_predicates(getattr(stmt, "whereclause", None))
            if cls is not None:
                doomed = [oid for oid, o in list(self._store[cls].items())
                          if _obj_matches(o, preds)]
                for oid in doomed:
                    await self.delete(self._store[cls][oid])
            return FakeResult([])

        # update(Model).where(...).values(...): mutate matching rows.
        if isinstance(stmt, Update):
            table_key = getattr(getattr(stmt, "table", None), "key", None)
            cls = next((c for c in self._store
                        if table_key and getattr(c, "__table__", None) is not None
                        and c.__table__.key == table_key), None)
            preds = _extract_predicates(getattr(stmt, "whereclause", None))
            if cls is not None:
                values = {
                    getattr(entry, "key", None) or str(entry): _unwrap_param(value)
                    for entry, value in stmt._values.items()
                }
                for o in self._store[cls].values():
                    if _obj_matches(o, preds):
                        for col_key, value in values.items():
                            if hasattr(o, col_key):
                                setattr(o, col_key, value)
            return FakeResult([])

        cds = stmt.column_descriptions
        entity = cds[0].get("entity")
        expr = cds[0].get("expr")
        preds = _extract_predicates(getattr(stmt, "whereclause", None))

        def matches(obj):
            return _obj_matches(obj, preds)

        def iter_expr_parts(node):
            """Flatten function args / groupings into leaf column-like nodes."""
            if node is None:
                return
            if isinstance(node, (tuple, list)):
                for child in node:
                    yield from iter_expr_parts(child)
            elif isinstance(node, FunctionElement):
                yield from iter_expr_parts(getattr(node, "clause_expr", None))
            else:
                element = getattr(node, "element", None)
                if element is not None and element is not node:
                    yield from iter_expr_parts(element)
                else:
                    children = (list(node.get_children())
                                if hasattr(node, "get_children")
                                and not isinstance(node, BinaryExpression) else [])
                    if children:
                        for child in children:
                            yield from iter_expr_parts(child)
                    else:
                        yield node

        def class_from_where(whereclause):
            """Resolve a model class from a whereclause's left-hand columns."""
            found = []

            def table_class(table_key):
                for stored_cls in self._store:
                    if table_key and getattr(stored_cls, "__table__", None) is not None \
                            and stored_cls.__table__.key == table_key:
                        return stored_cls
                return None

            def walk(node):
                if node is None:
                    return
                if isinstance(node, BooleanClauseList):
                    for child in node.get_children():
                        walk(child)
                elif isinstance(node, BinaryExpression):
                    left = node.left
                    cls = getattr(getattr(left, "parent", None), "class_", None)
                    if cls is None:
                        cls = table_class(getattr(getattr(left, "table", None), "key", None))
                    if cls is not None:
                        found.append(cls)

            walk(whereclause)
            return found[0] if found else None

        def agg_info(fn, whereclause=None):
            """Resolve (agg_name, model_class, column_key) for a function node."""
            name = getattr(fn, "name", None)
            if name == "coalesce":
                for part in iter_expr_parts(fn):
                    if isinstance(part, FunctionElement):
                        inner = agg_info(part, whereclause)
                        if inner:
                            return inner
                return None
            if name not in ("count", "sum", "avg", "max", "min"):
                return None
            for el in iter_expr_parts(getattr(fn, "clause_expr", None)):
                if isinstance(el, FunctionElement):
                    continue
                cls = getattr(getattr(el, "parent", None), "class_", None)
                if cls is None:
                    table_key = getattr(getattr(el, "table", None), "key", None)
                    for stored_cls in self._store:
                        if table_key and getattr(stored_cls, "__table__", None) is not None \
                                and stored_cls.__table__.key == table_key:
                            cls = stored_cls
                            break
                if cls is not None:
                    return (name, cls, getattr(el, "key", None))
            # Bare count(*) / count() with only a whereclause to work from.
            if name == "count":
                cls = class_from_where(whereclause)
                if cls is not None:
                    return (name, cls, None)
            return (name, entity, None)

        # Single-column aggregate selects: func.count/sum/avg/max/min(+coalesce).
        if len(cds) == 1:
            info = agg_info(expr, getattr(stmt, "whereclause", None))
            if info:
                name, cls, col_key = info
                if cls is None:
                    return FakeResult([])
                matched = [o for o in self._store[cls].values() if matches(o)]
                if name == "count":
                    rows = [len(matched)]
                else:
                    vals = [getattr(o, col_key) for o in matched if col_key and getattr(o, col_key) is not None]
                    if name == "sum":
                        rows = [sum(vals)]
                    elif name == "avg":
                        rows = [sum(vals) / len(vals)] if vals else [None]
                    else:
                        rows = [max(vals) if name == "max" else min(vals)] if vals else [None]
                return FakeResult(rows)

        # Multi-column selects: rows are tuples of column values. When an
        # aggregate column is present (e.g. group_by queries), group the
        # matched rows by the plain columns and compute per-group aggregates.
        if len(cds) >= 2:
            plain_keys = [cd["expr"].key for cd in cds
                          if not isinstance(cd["expr"], FunctionElement) and cd["expr"].key]
            agg_columns = [(i, agg_info(cd["expr"])) for i, cd in enumerate(cds)
                           if isinstance(cd["expr"], FunctionElement)]
            agg_columns = [(i, info) for i, info in agg_columns if info]
            # When the select has no FROM (pure aggregates with a whereclause),
            # resolve the row source from the predicate columns.
            row_cls = entity or class_from_where(getattr(stmt, "whereclause", None))
            if row_cls is not None:
                rows = [o for o in self._store[row_cls].values() if matches(o)]
            else:
                rows = []
            if agg_columns and rows:
                groups = defaultdict(list)
                for o in rows:
                    groups[tuple(getattr(o, k, None) for k in plain_keys)].append(o)
                out = []
                for key, members in groups.items():
                    row = list(key)
                    for i, (name, _cls, col_key) in agg_columns:
                        if name == "count":
                            row.append(len(members))
                        else:
                            vals = [getattr(o, col_key) for o in members if col_key and getattr(o, col_key) is not None]
                            if name == "sum":
                                row.append(sum(vals))
                            elif name == "avg":
                                row.append(sum(vals) / len(vals) if vals else None)
                            elif name == "max":
                                row.append(max(vals) if vals else None)
                            else:
                                row.append(min(vals) if vals else None)
                    out.append(tuple(row))
                return FakeResult(out)
            # Pure aggregates with no matching rows still yield one NULL row.
            if agg_columns and not rows and not plain_keys:
                return FakeResult([tuple(0 if name == "count" else None
                                         for _i, (name, _cls, _col) in agg_columns)])
            return FakeResult([tuple(getattr(o, k, None) for k in plain_keys) for o in rows])

        if entity is not None:
            rows = []
            for obj in self._store[entity].values():
                if _obj_matches(obj, preds):
                    rows.append(obj)
            for clause in reversed(getattr(stmt, "_order_by_clauses", ())):
                element = getattr(clause, "element", None)
                col = element if element is not None else clause
                key = getattr(col, "key", None)
                if key:
                    descending = " DESC" in str(clause).upper()
                    if descending:
                        rows.sort(key=lambda o, k=key: (getattr(o, k) is not None, getattr(o, k)))
                        rows.reverse()
                    else:
                        rows.sort(key=lambda o, k=key: (getattr(o, k) is None, getattr(o, k)))
            offset = getattr(stmt, "_offset", None)
            if offset is not None and offset > 0:
                rows = rows[offset:]
            limit = getattr(stmt, "_limit", None)
            if limit is not None:
                rows = rows[:limit]
            # Column-only selects (e.g. select(Model.col)) yield 1-element
            # rows like SQLAlchemy's Row, so row[0] unpacking works.
            if len(stmt.column_descriptions) == 1:
                key = getattr(expr, "key", None)
                if isinstance(key, str):
                    rows = [(getattr(obj, key, None),) for obj in rows]
            # selectinload(Rel): relationships cannot be auto-loaded here, but
            # the response schemas expect the attribute to exist.
            for opt in getattr(stmt, "_options", ()):
                rel_name = getattr(opt, "key", None)
                if rel_name:
                    for obj in rows:
                        if not hasattr(obj, rel_name):
                            setattr(obj, rel_name, [])
        return FakeResult(rows)

    async def get(self, model, ident):
        return self._store[model].get(ident)

    async def merge(self, obj):
        self.add(obj)
        return obj

    async def scalar(self, stmt, *_args, **_kwargs):
        result = await self.execute(stmt)
        return result.scalar()

    async def delete(self, obj):
        if getattr(obj, "id", None) in self._store.get(type(obj), {}):
            self._removed[type(obj)][obj.id] = obj
            del self._store[type(obj)][obj.id]

    async def flush(self):
        pass

    async def commit(self):
        pass

    async def rollback(self):
        pass

    async def refresh(self, _obj, *a, **k):
        pass

    async def close(self):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        pass
