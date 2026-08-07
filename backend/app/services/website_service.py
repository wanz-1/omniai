import json
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.website import Website, WebsiteDeployment
from app.schemas.website import WebsiteDeployRequest, WebsiteGenerateRequest, WebsitePublishRequest
from app.services.ai_service import ai_service
from app.services.template_service import TEMPLATES


class WebsiteService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate(self, website_id: uuid.UUID, user_id: uuid.UUID, body: WebsiteGenerateRequest) -> dict:
        website = await self.db.get(Website, website_id)
        if not website or website.user_id != user_id:
            raise NotFoundError("Website", str(website_id))

        template = TEMPLATES.get(website.template_id or "")
        template_structure = template["structure"] if template else {}

        prompt = f"""You are a professional website builder. Generate a complete {website.framework.value} website with {website.styling.value} CSS based on the following description:

Description: {body.prompt}

Framework: {website.framework.value}
Styling: {website.styling.value}

Return the response as JSON with this structure:
{{
  "pages": [
    {{
      "slug": "index",
      "title": "Home",
      "sections": [
        {{"type": "hero", "content": {{"heading": "...", "subheading": "...", "cta": "..."}}}},
        {{"type": "features", "content": {{"items": [{{"title": "...", "description": "..."}}]}}}},
        {{"type": "about", "content": {{"text": "..."}}}},
        {{"type": "contact", "content": {{"email": "...", "phone": "..."}}}}
      ]
    }}
  ],
  "theme": {{
    "primary_color": "#2563EB",
    "secondary_color": "#7C3AED",
    "font": "Inter",
    "dark_mode": true
  }}
}}

Only return valid JSON. No markdown. No explanations."""

        response = await ai_service.complete(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            model="gpt-4o",
        )

        try:
            generated = json.loads(response["content"])
        except json.JSONDecodeError:
            generated = {"pages": [], "theme": {}}

        website.pages = generated.get("pages", template_structure.get("pages", []))
        website.theme_config = generated.get("theme", template_structure.get("theme", {}))
        website.deployment_status = "draft"
        await self.db.flush()

        return {
            "website_id": str(website.id),
            "pages": website.pages,
            "theme": website.theme_config,
            "framework": website.framework.value,
            "styling": website.styling.value,
        }

    def _render_section(self, section: dict, theme: dict) -> str:
        primary = theme.get("primary_color", "#2563EB")
        secondary = theme.get("secondary_color", "#7C3AED")
        dark_mode = theme.get("dark_mode", False)
        card_bg = "#1E293B" if dark_mode else "#FFFFFF"
        muted = "#94A3B8" if dark_mode else "#64748B"
        border = "#334155" if dark_mode else "#E2E8F0"

        t = section.get("type", "")
        c = section.get("content", {})

        if t == "hero":
            return f"""<section style="background:linear-gradient(135deg,{primary},{secondary});color:#fff;padding:100px 20px;text-align:center;">
                <div style="max-width:800px;margin:0 auto;">
                <h1 style="font-size:3em;margin-bottom:20px;">{c.get('heading','Welcome')}</h1>
                <p style="font-size:1.2em;margin-bottom:30px;opacity:0.9;">{c.get('subheading','')}</p>
                <a href="#" style="background:#fff;color:{primary};padding:15px 30px;border-radius:8px;text-decoration:none;font-weight:bold;display:inline-block;">{c.get('cta','Get Started')}</a>
                </div></section>"""

        if t == "features":
            items = c.get("items", [])
            cards = "".join(
                f'<div style="background:{card_bg};border:1px solid {border};border-radius:12px;padding:24px;text-align:center;">'
                f'<div style="width:48px;height:48px;border-radius:12px;background:{primary}20;color:{primary};display:flex;align-items:center;justify-content:center;margin:0 auto 12px;font-size:1.5em;">{i.get("icon","★")}</div>'
                f'<h3 style="margin-bottom:8px;">{i["title"]}</h3>'
                f'<p style="color:{muted};font-size:0.9em;">{i.get("description","")}</p></div>'
                for i in items
            )
            return f'<section style="padding:80px 20px;"><div style="max-width:1200px;margin:0 auto;"><h2 style="text-align:center;margin-bottom:40px;">{c.get("heading","Features")}</h2><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:24px;">{cards}</div></div></section>'

        if t == "about":
            return f"""<section style="padding:80px 20px;background:{card_bg};"><div style="max-width:800px;margin:0 auto;text-align:center;">
                <h2 style="margin-bottom:20px;">{c.get('heading','About')}</h2>
                <p style="color:{muted};line-height:1.8;">{c.get('text','')}</p>
                {f'<p style="color:{muted};margin-top:16px;"><strong>Mission:</strong> {c.get("mission","")}</p>' if c.get('mission') else ''}
                {f'<p style="color:{muted};margin-top:8px;"><strong>Vision:</strong> {c.get("vision","")}</p>' if c.get('vision') else ''}
            </div></section>"""

        if t == "contact":
            return f"""<section style="padding:80px 20px;"><div style="max-width:600px;margin:0 auto;text-align:center;">
                <h2 style="margin-bottom:24px;">{c.get('heading','Contact Us')}</h2>
                <div style="display:flex;flex-direction:column;gap:12px;color:{muted};">
                {f'<p>📧 {c["email"]}</p>' if c.get('email') else ''}
                {f'<p>📞 {c["phone"]}</p>' if c.get('phone') else ''}
                {f'<p>📍 {c["address"]}</p>' if c.get('address') else ''}
                </div>
                <a href="#" style="display:inline-block;margin-top:24px;background:{primary};color:#fff;padding:12px 24px;border-radius:8px;text-decoration:none;">{c.get('cta','Send Message')}</a>
            </div></section>"""

        if t == "cta":
            return f"""<section style="padding:80px 20px;background:linear-gradient(135deg,{primary},{secondary});color:#fff;text-align:center;">
                <div style="max-width:600px;margin:0 auto;">
                <h2 style="margin-bottom:16px;">{c.get('heading','Ready to Start?')}</h2>
                <p style="margin-bottom:24px;opacity:0.9;">{c.get('text','')}</p>
                <a href="#" style="background:#fff;color:{primary};padding:14px 28px;border-radius:8px;text-decoration:none;font-weight:bold;">{c.get('button_text','Get Started')}</a>
                </div></section>"""

        if t in ("content", "text"):
            return f"""<section style="padding:80px 20px;"><div style="max-width:800px;margin:0 auto;">
                <h2 style="margin-bottom:16px;">{c.get('title','')}</h2>
                <div style="color:{muted};line-height:1.8;">{c.get('body','')}</div>
            </div></section>"""

        if t == "stats":
            items = c.get("items", [])
            stat_cards = "".join(
                f'<div style="text-align:center;"><div style="font-size:2.5em;font-weight:bold;color:{primary};">{i.get("value","")}</div><div style="color:{muted};margin-top:4px;">{i.get("label","")}</div></div>'
                for i in items
            )
            return f'<section style="padding:60px 20px;background:{card_bg};"><div style="max-width:1000px;margin:0 auto;display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:32px;">{stat_cards}</div></section>'

        if t == "team":
            items = c.get("items", [])
            cards = "".join(
                f'<div style="background:{card_bg};border:1px solid {border};border-radius:12px;padding:24px;text-align:center;">'
                f'<div style="width:80px;height:80px;border-radius:50%;background:linear-gradient(135deg,{primary},{secondary});margin:0 auto 12px;display:flex;align-items:center;justify-content:center;color:#fff;font-size:2em;font-weight:bold;">{i.get("name","")[0] if i.get("name") else "?"}</div>'
                f'<h4>{i.get("name","")}</h4>'
                f'<p style="color:{muted};font-size:0.85em;">{i.get("role","")}</p>'
                f'<p style="color:{muted};font-size:0.8em;margin-top:8px;">{i.get("bio","")}</p></div>'
                for i in items
            )
            return f'<section style="padding:80px 20px;"><div style="max-width:1200px;margin:0 auto;"><h2 style="text-align:center;margin-bottom:40px;">{c.get("heading","Our Team")}</h2><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:24px;">{cards}</div></div></section>'

        if t == "testimonials":
            items = c.get("items", [])
            cards = "".join(
                f'<div style="background:{card_bg};border:1px solid {border};border-radius:12px;padding:24px;position:relative;">'
                f'<div style="font-size:3em;color:{primary}20;position:absolute;top:8px;left:16px;">"</div>'
                f'<p style="color:{muted};font-style:italic;margin-bottom:16px;position:relative;z-index:1;">{i.get("quote","")}</p>'
                f'<div><strong>{i.get("author","")}</strong><span style="color:{muted};font-size:0.85em;"> — {i.get("role","")}</span></div></div>'
                for i in items
            )
            return f'<section style="padding:80px 20px;background:{card_bg};"><div style="max-width:1000px;margin:0 auto;"><h2 style="text-align:center;margin-bottom:40px;">{c.get("heading","Testimonials")}</h2><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:24px;">{cards}</div></div></section>'

        if t == "pricing":
            items = c.get("items", [])
            cards = "".join(
                f'<div style="background:{card_bg};border:2px solid {"transparent" if not i.get("featured") else primary};border-radius:16px;padding:32px;text-align:center;{f"box-shadow:0 8px 32px {primary}20;" if i.get("featured") else ""}>'
                f'<h3 style="margin-bottom:8px;">{i.get("name","")}</h3>'
                f'<div style="font-size:2.5em;font-weight:bold;color:{primary};margin-bottom:16px;">{i.get("price","")}</div>'
                f'<ul style="list-style:none;padding:0;margin-bottom:24px;text-align:left;">'
                + "".join(f'<li style="padding:6px 0;color:{muted};">✓ {f}</li>' for f in i.get("features", []))
                + f'</ul>'
                f'<a href="#" style="display:block;background:{primary};color:#fff;padding:12px;border-radius:8px;text-decoration:none;">{i.get("cta","Choose Plan")}</a></div>'
                for i in items
            )
            return f'<section style="padding:80px 20px;"><div style="max-width:1200px;margin:0 auto;"><h2 style="text-align:center;margin-bottom:40px;">{c.get("heading","Pricing")}</h2><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:24px;">{cards}</div></div></section>'

        if t == "faq":
            items = c.get("items", [])
            faq_items = "".join(
                f'<details style="background:{card_bg};border:1px solid {border};border-radius:8px;padding:16px;margin-bottom:8px;">'
                f'<summary style="font-weight:600;cursor:pointer;">{i.get("question","")}</summary>'
                f'<p style="color:{muted};margin-top:12px;">{i.get("answer","")}</p></details>'
                for i in items
            )
            return f'<section style="padding:80px 20px;"><div style="max-width:700px;margin:0 auto;"><h2 style="text-align:center;margin-bottom:32px;">{c.get("heading","FAQ")}</h2>{faq_items}</div></section>'

        if t == "gallery":
            items = c.get("images", [])
            images = "".join(
                f'<div style="border-radius:12px;overflow:hidden;background:{card_bg};"><div style="height:200px;background:linear-gradient(135deg,{primary}40,{secondary}40);display:flex;align-items:center;justify-content:center;color:{muted};">{i.get("alt","Image")}</div>'
                f'<div style="padding:12px;"><p style="font-size:0.85em;color:{muted};">{i.get("caption","")}</p></div></div>'
                for i in items
            )
            return f'<section style="padding:80px 20px;"><div style="max-width:1200px;margin:0 auto;"><h2 style="text-align:center;margin-bottom:40px;">{c.get("heading","Gallery")}</h2><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:16px;">{images}</div></div></section>'

        if t == "blog":
            posts = c.get("posts", [])
            cards = "".join(
                f'<div style="background:{card_bg};border:1px solid {border};border-radius:12px;overflow:hidden;">'
                f'<div style="height:180px;background:linear-gradient(135deg,{secondary}40,{primary}40);"></div>'
                f'<div style="padding:20px;">'
                f'<h3 style="margin-bottom:8px;">{p.get("title","")}</h3>'
                f'<p style="color:{muted};font-size:0.85em;margin-bottom:12px;">{p.get("excerpt","")}</p>'
                f'<div style="display:flex;justify-content:space-between;font-size:0.8em;color:{muted};">'
                f'<span>{p.get("date","")}</span><span>{p.get("author","")}</span></div></div></div>'
                for p in posts
            )
            return f'<section style="padding:80px 20px;"><div style="max-width:1200px;margin:0 auto;"><h2 style="text-align:center;margin-bottom:40px;">{c.get("heading","Blog")}</h2><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:24px;">{cards}</div></div></section>'

        if t == "footer":
            return f"""<footer style="padding:40px 20px;background:{card_bg};border-top:1px solid {border};text-align:center;">
                <p style="color:{muted};">{c.get('text','© All rights reserved.')}</p>
                <div style="display:flex;justify-content:center;gap:16px;margin-top:12px;">
                {"".join(f'<a href="{link.get("url","#")}" style="color:{muted};text-decoration:none;font-size:0.85em;">{link.get("label","Link")}</a>' for link in c.get("links",[]))}
                </div></footer>"""

        return ""

    async def generate_preview(self, website_id: uuid.UUID, user_id: uuid.UUID) -> str:
        website = await self.db.get(Website, website_id)
        if not website or website.user_id != user_id:
            raise NotFoundError("Website", str(website_id))

        website.deployment_status = "building"
        await self.db.flush()

        pages = website.pages or []
        theme = website.theme_config or {}
        font = theme.get("font", "Inter")
        dark_mode = theme.get("dark_mode", False)
        bg_color = "#0F172A" if dark_mode else "#F8FAFC"
        text_color = "#F8FAFC" if dark_mode else "#111827"

        nav_html = ""
        if len(pages) > 1:
            nav_items = "".join(
                f'<a href="#{p.get("slug","")}" style="color:{text_color};text-decoration:none;font-size:0.9em;padding:8px 16px;border-radius:6px;transition:background 0.2s;">{p.get("title","Page")}</a>'
                for p in pages
            )
            nav_html = f'<nav style="position:sticky;top:0;background:{bg_color}cc;backdrop-filter:blur(12px);border-bottom:1px solid #e2e8f020;padding:12px 24px;display:flex;align-items:center;justify-content:space-between;z-index:100;"><span style="font-weight:700;font-size:1.1em;">{website.name}</span><div style="display:flex;gap:4px;">{nav_items}</div></nav>'

        sections_html = ""
        for page in pages:
            page_id = page.get("slug", "")
            for section in page.get("sections", []):
                html = self._render_section(section, theme)
                if html:
                    sections_html += f'<div id="{page_id}">{html}</div>'

        html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<link href="https://fonts.googleapis.com/css2?family={font.replace(' ', '+')}:wght@300;400;600;700;800&display=swap" rel="stylesheet">
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css" rel="stylesheet">
<style>
* {{margin:0;padding:0;box-sizing:border-box;}}
body {{font-family:'{font}',sans-serif;background:{bg_color};color:{text_color};}}
section {{animation:fadeIn 0.5s ease;}}
@keyframes fadeIn {{from{{opacity:0;transform:translateY(20px)}}to{{opacity:1;transform:translateY(0)}}}}
a {{transition:all 0.2s;}}
a:hover {{opacity:0.8;transform:translateY(-1px);}}
details[open] summary {{margin-bottom:8px;}}
</style>
</head>
<body>{nav_html}<main>{sections_html}</main></body></html>"""

        import hashlib
        preview_id = hashlib.sha256(str(website_id).encode()).hexdigest()[:12]
        preview_url = f"/preview/{preview_id}"

        website.preview_url = preview_url
        website.generated_code_path = f"websites/{website_id}/index.html"
        website.deployment_status = "draft"
        await self.db.flush()

        return preview_url

    async def publish(self, website_id: uuid.UUID, user_id: uuid.UUID, body: WebsitePublishRequest) -> dict:
        website = await self.db.get(Website, website_id)
        if not website or website.user_id != user_id:
            raise NotFoundError("Website", str(website_id))

        website.is_published = True
        website.custom_domain = body.custom_domain
        website.published_url = f"https://{body.subdomain or str(website_id)[:8]}.omniai.app"
        website.deployment_status = "deployed"
        await self.db.flush()

        return {
            "published_url": website.published_url,
            "deployment_status": "deployed",
        }

    async def deploy(self, website_id: uuid.UUID, user_id: uuid.UUID, body: WebsiteDeployRequest) -> dict:
        website = await self.db.get(Website, website_id)
        if not website or website.user_id != user_id:
            raise NotFoundError("Website", str(website_id))

        deployment = WebsiteDeployment(
            website_id=website.id,
            platform=body.platform,
            status="deploying",
        )
        self.db.add(deployment)

        website.deployment_status = "building"
        await self.db.flush()

        deployment.status = "deployed"
        deployment.url = f"https://{str(website_id)[:8]}.{body.platform}.app"
        website.deployment_status = "deployed"
        website.published_url = deployment.url
        await self.db.flush()

        return {
            "deployment_id": str(deployment.id),
            "url": deployment.url,
            "status": "deployed",
        }

    async def generate_branding(self, body) -> dict:
        prompt = f"""You are an expert branding consultant. Based on the following description, generate branding assets.

Description: {body.prompt}
{f'Industry: {body.industry}' if body.industry else ''}

Return ONLY valid JSON with this structure:
{{
  "brand_names": ["Name1", "Name2", "Name3", "Name4", "Name5"],
  "taglines": ["Tagline1", "Tagline2", "Tagline3"],
  "color_palettes": [
    {{"name": "Modern", "colors": ["#hex1", "#hex2", "#hex3", "#hex4"]}},
    {{"name": "Classic", "colors": ["#hex1", "#hex2", "#hex3", "#hex4"]}}
  ],
  "logo_concepts": ["Concept1: description", "Concept2: description", "Concept3: description"],
  "business_descriptions": ["Short description 1", "Short description 2"]
}}

Only return valid JSON. No markdown. No explanations."""

        response = await ai_service.complete(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            model="gpt-4o",
        )

        try:
            content = response["content"]
            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1] if "\n" in content else content
                content = content.rsplit("```", 1)[0] if "```" in content else content
            result = json.loads(content)
        except (json.JSONDecodeError, KeyError):
            result = {}

        return {
            "brand_names": result.get("brand_names", []),
            "taglines": result.get("taglines", []),
            "color_palettes": result.get("color_palettes", []),
            "logo_concepts": result.get("logo_concepts", []),
            "business_descriptions": result.get("business_descriptions", []),
        }

    async def export_site(self, website_id: uuid.UUID, user_id: uuid.UUID, body) -> tuple[bytes, str, str]:
        website = await self.db.get(Website, website_id)
        if not website or website.user_id != user_id:
            raise NotFoundError("Website", str(website_id))

        pages = website.pages or []
        theme = website.theme_config or {}

        nav_items = "".join(
            f'<a href="#{p.get("slug","")}" style="color:#fff;text-decoration:none;padding:8px 16px;">{p.get("title","Page")}</a>'
            for p in pages
        )

        sections_html = ""
        for page in pages:
            for section in page.get("sections", []):
                sections_html += self._render_section(section, theme)

        font = theme.get("font", "Inter")
        primary = theme.get("primary_color", "#2563EB")
        secondary = theme.get("secondary_color", "#7C3AED")
        dark_mode = theme.get("dark_mode", False)
        bg = "#0F172A" if dark_mode else "#F8FAFC"

        html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{website.name}</title>
<link href="https://fonts.googleapis.com/css2?family={font.replace(' ', '+')}:wght@300;400;600;700;800&display=swap" rel="stylesheet">
<style>
* {{margin:0;padding:0;box-sizing:border-box;}}
body {{font-family:'{font}',sans-serif;background:{bg};color:{'#F8FAFC' if dark_mode else '#111827'};}}
a {{transition:all 0.2s;}} a:hover {{opacity:0.8;}}
</style>
</head>
<body><nav style="background:{bg};padding:16px 24px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #e2e8f020;"><span style="font-weight:700;font-size:1.2em;background:linear-gradient(135deg,{primary},{secondary});-webkit-background-clip:text;-webkit-text-fill-color:transparent;">{website.name}</span><div>{nav_items}</div></nav><main>{sections_html}</main></body></html>"""

        content = html.encode("utf-8")
        filename = f"{website.name.replace(' ', '_').lower()}.html"
        return content, "text/html", filename
