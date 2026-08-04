"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { apiClient } from "@/lib/api-client";
import { toast } from "sonner";
import { Check, Loader2, CreditCard, FileText, Clock } from "lucide-react";

interface Plan {
  id: string;
  name: string;
  slug: string;
  description: string;
  price_monthly: number;
  price_yearly: number;
  currency: string;
  credits_monthly: number;
  max_users: number;
  max_projects: number;
  max_agents: number;
  max_api_requests: number;
  max_storage_mb: number;
  features: string[];
  is_active: boolean;
  sort_order: number;
}

interface Subscription {
  id: string;
  organization_id: string;
  plan_id: string;
  status: string;
  interval: string;
  current_period_end: string | null;
  plan: Plan | null;
}

interface Invoice {
  id: string;
  amount: number;
  currency: string;
  status: string;
  paid_at: string | null;
  created_at: string;
}

export default function BillingPage() {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [checkoutLoading, setCheckoutLoading] = useState<string | null>(null);
  const [interval, setInterval] = useState<"monthly" | "yearly">("monthly");

  useEffect(() => {
    loadBillingData();
  }, []);

  const loadBillingData = async () => {
    setLoading(true);
    try {
      const plansRes = await apiClient.get("/billing/plans");
      setPlans(plansRes.data);

      try {
        const orgsRes = await apiClient.get("/organizations");
        const orgs = orgsRes.data;
        if (orgs.length > 0) {
          const orgId = orgs[0].id;
          const subRes = await apiClient.get(`/billing/subscriptions/${orgId}`);
          setSubscription(subRes.data);

          const invRes = await apiClient.get(`/billing/invoices/${orgId}`);
          setInvoices(invRes.data);
        }
      } catch {
        // No org yet
      }
    } catch {
      toast.error("Failed to load billing data");
    } finally {
      setLoading(false);
    }
  };

  const handleSubscribe = async (plan: Plan) => {
    setCheckoutLoading(plan.id);
    try {
      const orgsRes = await apiClient.get("/organizations");
      const orgs = orgsRes.data;
      if (orgs.length === 0) {
        toast.error("Create an organization first");
        return;
      }

      const res = await apiClient.post("/billing/checkout", {
        plan_id: plan.id,
        interval,
        organization_id: orgs[0].id,
        success_url: `${window.location.origin}/billing?success=true`,
        cancel_url: `${window.location.origin}/billing?canceled=true`,
      });
      window.location.href = res.data.url;
    } catch {
      toast.error("Failed to start checkout");
    } finally {
      setCheckoutLoading(null);
    }
  };

  const handleManageBilling = async () => {
    try {
      const orgsRes = await apiClient.get("/organizations");
      const orgs = orgsRes.data;
      if (orgs.length === 0) return;

      const res = await apiClient.post("/billing/portal", {
        organization_id: orgs[0].id,
        return_url: window.location.href,
      });
      window.location.href = res.data.url;
    } catch {
      toast.error("Failed to open billing portal");
    }
  };

  const activePlan = subscription?.plan;
  const isFree = !subscription || subscription.status !== "active";

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Billing & Plans</h1>
          <p className="text-muted-foreground mt-1">Manage your subscription and view invoices</p>
        </div>
        {subscription && (
          <Button variant="outline" onClick={handleManageBilling}>
            <CreditCard className="w-4 h-4 mr-2" />
            Manage Billing
          </Button>
        )}
      </div>

      {activePlan && (
        <Card className="bg-primary/5 border-primary/20">
          <CardContent className="flex items-center justify-between py-4">
            <div>
              <p className="text-sm text-muted-foreground">Current Plan</p>
              <p className="text-xl font-bold">{activePlan.name}</p>
              <p className="text-sm text-muted-foreground">
                {subscription?.interval === "yearly" ? "Yearly" : "Monthly"} &middot;{" "}
                <Badge variant={subscription?.status === "active" ? "success" : "warning"}>
                  {subscription?.status}
                </Badge>
              </p>
            </div>
            <div className="text-right">
              <p className="text-2xl font-bold">
                ${subscription?.interval === "yearly" ? activePlan.price_yearly : activePlan.price_monthly}
              </p>
              <p className="text-sm text-muted-foreground">
                /{subscription?.interval === "yearly" ? "year" : "month"}
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="flex items-center gap-2 mb-4">
        <Button
          variant={interval === "monthly" ? "primary" : "outline"}
          size="sm"
          onClick={() => setInterval("monthly")}
        >
          Monthly
        </Button>
        <Button
          variant={interval === "yearly" ? "primary" : "outline"}
          size="sm"
          onClick={() => setInterval("yearly")}
        >
          Yearly <Badge variant="success" className="ml-1">Save ~17%</Badge>
        </Button>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {plans.map((plan) => {
          const isActivePlan = activePlan?.id === plan.id;
          const price = interval === "yearly" ? plan.price_yearly : plan.price_monthly;

          return (
            <Card key={plan.id} className={`relative flex flex-col ${isActivePlan ? "ring-2 ring-primary" : ""}`}>
              {plan.slug === "pro" && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <Badge variant="default">Most Popular</Badge>
                </div>
              )}
              <CardHeader>
                <CardTitle>{plan.name}</CardTitle>
                <CardDescription>{plan.description}</CardDescription>
                <div className="mt-4">
                  <span className="text-3xl font-bold">${price}</span>
                  <span className="text-muted-foreground ml-1">
                    /{interval === "yearly" ? "year" : "month"}
                  </span>
                </div>
              </CardHeader>
              <CardContent className="flex-1">
                <ul className="space-y-2">
                  {(plan.features || []).map((feature, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm">
                      <Check className="w-4 h-4 text-green-500 mt-0.5 shrink-0" />
                      <span>{feature}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
              <CardFooter>
                {isActivePlan ? (
                  <Button className="w-full" variant="outline" disabled>
                    Current Plan
                  </Button>
                ) : (
                  <Button
                    className="w-full"
                    onClick={() => handleSubscribe(plan)}
                    isLoading={checkoutLoading === plan.id}
                    variant={plan.price_monthly === 0 ? "outline" : "primary"}
                  >
                    {plan.price_monthly === 0 ? "Get Started" : `Subscribe`}
                  </Button>
                )}
              </CardFooter>
            </Card>
          );
        })}
      </div>

      {invoices.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5" />
              Invoices
            </CardTitle>
            <CardDescription>Your recent billing invoices</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {invoices.map((inv) => (
                <div
                  key={inv.id}
                  className="flex items-center justify-between p-3 bg-muted/50 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <FileText className="w-4 h-4 text-muted-foreground" />
                    <div>
                      <p className="text-sm font-medium">
                        ${inv.amount} {inv.currency}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {inv.created_at ? new Date(inv.created_at).toLocaleDateString() : ""}
                      </p>
                    </div>
                  </div>
                  <Badge variant={inv.status === "paid" ? "success" : "warning"}>
                    {inv.status}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
