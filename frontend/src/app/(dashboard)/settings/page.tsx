"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { useAuth } from "@/hooks/useAuth";
import { apiClient } from "@/lib/api-client";
import { toast } from "sonner";
import { Key, Shield, Smartphone, LogOut, Copy, Check, Eye, EyeOff } from "lucide-react";

export default function SettingsPage() {
  const { user, refresh } = useAuth();
  const [displayName, setDisplayName] = useState(user?.display_name || "");
  const [bio, setBio] = useState("");
  const [loading, setLoading] = useState(false);

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [passwordLoading, setPasswordLoading] = useState(false);

  const [twoFactorSecret, setTwoFactorSecret] = useState("");
  const [twoFactorCode, setTwoFactorCode] = useState("");
  const [twoFactorLoading, setTwoFactorLoading] = useState(false);
  const [twoFactorEnabled, setTwoFactorEnabled] = useState(user?.two_factor_enabled || false);
  const [showQr, setShowQr] = useState(false);
  const [copied, setCopied] = useState(false);

  const [sessions, setSessions] = useState<any[]>([]);
  const [sessionsLoading, setSessionsLoading] = useState(false);

  useEffect(() => {
    if (user) {
      setDisplayName(user.display_name);
      setTwoFactorEnabled(user.two_factor_enabled);
    }
  }, [user]);

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    setSessionsLoading(true);
    try {
      const res = await apiClient.get("/auth/sessions");
      setSessions(res.data);
    } catch {
      // ignore
    } finally {
      setSessionsLoading(false);
    }
  };

  const handleSaveProfile = async () => {
    setLoading(true);
    try {
      await apiClient.put("/users/me", { display_name: displayName, bio });
      toast.success("Profile updated");
      refresh();
    } catch {
      toast.error("Failed to update profile");
    } finally {
      setLoading(false);
    }
  };

  const handleChangePassword = async () => {
    if (!currentPassword || !newPassword) {
      toast.error("Fill in both password fields");
      return;
    }
    if (newPassword.length < 8) {
      toast.error("New password must be at least 8 characters");
      return;
    }
    setPasswordLoading(true);
    try {
      await apiClient.post("/auth/me/password", {
        current_password: currentPassword,
        new_password: newPassword,
      });
      toast.success("Password changed");
      setCurrentPassword("");
      setNewPassword("");
    } catch {
      toast.error("Failed to change password");
    } finally {
      setPasswordLoading(false);
    }
  };

  const handleSetup2FA = async () => {
    setTwoFactorLoading(true);
    try {
      const res = await apiClient.post("/auth/2fa/setup");
      setTwoFactorSecret(res.data.secret);
      setShowQr(true);
    } catch {
      toast.error("Failed to setup 2FA");
    } finally {
      setTwoFactorLoading(false);
    }
  };

  const handleVerify2FA = async () => {
    if (!twoFactorCode || twoFactorCode.length !== 6) {
      toast.error("Enter a valid 6-digit code");
      return;
    }
    setTwoFactorLoading(true);
    try {
      await apiClient.post("/auth/2fa/verify", {
        code: twoFactorCode,
        temp_token: twoFactorSecret,
      });
      toast.success("2FA enabled successfully");
      setTwoFactorEnabled(true);
      setShowQr(false);
      setTwoFactorCode("");
      refresh();
    } catch {
      toast.error("Invalid code. Make sure your authenticator app shows the correct code.");
    } finally {
      setTwoFactorLoading(false);
    }
  };

  const handleRevokeSession = async (sessionId: string) => {
    try {
      await apiClient.post(`/auth/sessions/${sessionId}/revoke`);
      toast.success("Session revoked");
      loadSessions();
    } catch {
      toast.error("Failed to revoke session");
    }
  };

  const copySecret = () => {
    navigator.clipboard.writeText(twoFactorSecret);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6 animate-fade-in max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-muted-foreground mt-1">Manage your account, security, and preferences</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Profile</CardTitle>
          <CardDescription>Update your personal information</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Input
            id="display_name"
            label="Display Name"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
          />
          <Input
            id="email"
            label="Email"
            value={user?.email || ""}
            disabled
          />
          <Input
            id="bio"
            label="Bio"
            value={bio}
            onChange={(e) => setBio(e.target.value)}
            placeholder="Tell us about yourself"
          />
          <Button onClick={handleSaveProfile} isLoading={loading}>
            Save Changes
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="w-5 h-5" />
            Security
          </CardTitle>
          <CardDescription>Manage your password and two-factor authentication</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-4">
            <h4 className="font-medium">Change Password</h4>
            <div className="relative">
              <Input
                id="current_password"
                label="Current Password"
                type={showPassword ? "text" : "password"}
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
              />
            </div>
            <div className="relative">
              <Input
                id="new_password"
                label="New Password"
                type={showPassword ? "text" : "password"}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-8 text-muted-foreground hover:text-foreground"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            <Button onClick={handleChangePassword} isLoading={passwordLoading} variant="outline" size="sm">
              <Key className="w-4 h-4 mr-2" />
              Change Password
            </Button>
          </div>

          <div className="border-t pt-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h4 className="font-medium">Two-Factor Authentication</h4>
                <p className="text-sm text-muted-foreground">
                  Add an extra layer of security to your account
                </p>
              </div>
              <Badge variant={twoFactorEnabled ? "success" : "outline"}>
                {twoFactorEnabled ? "Enabled" : "Disabled"}
              </Badge>
            </div>

            {!twoFactorEnabled && !showQr && (
              <Button onClick={handleSetup2FA} isLoading={twoFactorLoading} variant="outline" size="sm">
                <Smartphone className="w-4 h-4 mr-2" />
                Setup 2FA
              </Button>
            )}

            {showQr && (
              <div className="space-y-4 p-4 bg-muted/50 rounded-lg">
                <p className="text-sm">
                  Scan this secret with your authenticator app (Google Authenticator, Authy, etc.)
                </p>
                <div className="flex items-center gap-2">
                  <code className="flex-1 p-2 bg-background rounded text-xs font-mono break-all">
                    {twoFactorSecret}
                  </code>
                  <Button variant="ghost" size="sm" onClick={copySecret}>
                    {copied ? <Check className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4" />}
                  </Button>
                </div>
                <Input
                  id="2fa_code"
                  label="Authenticator Code"
                  value={twoFactorCode}
                  onChange={(e) => setTwoFactorCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                  placeholder="000000"
                  maxLength={6}
                />
                <div className="flex gap-2">
                  <Button onClick={handleVerify2FA} isLoading={twoFactorLoading} size="sm">
                    Verify & Enable
                  </Button>
                  <Button onClick={() => setShowQr(false)} variant="ghost" size="sm">
                    Cancel
                  </Button>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <LogOut className="w-5 h-5" />
            Active Sessions
          </CardTitle>
          <CardDescription>Manage your active login sessions</CardDescription>
        </CardHeader>
        <CardContent>
          {sessionsLoading ? (
            <p className="text-sm text-muted-foreground">Loading sessions...</p>
          ) : sessions.length === 0 ? (
            <p className="text-sm text-muted-foreground">No active sessions</p>
          ) : (
            <div className="space-y-3">
              {sessions.map((session: any) => (
                <div key={session.id} className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                  <div className="text-sm">
                    <p className="font-medium">{session.device_name || "Unknown device"}</p>
                    <p className="text-muted-foreground text-xs">
                      {session.ip_address || "Unknown IP"} &middot;{" "}
                      {session.last_activity_at
                        ? new Date(session.last_activity_at).toLocaleDateString()
                        : "No activity"}
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleRevokeSession(session.id)}
                  >
                    Revoke
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
