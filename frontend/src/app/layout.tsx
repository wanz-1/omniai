import type { Metadata } from "next";
import { Providers } from "@/providers";
import { AuthProvider } from "@/providers/AuthProvider";
import { Toaster } from "sonner";
import "@/styles/globals.css";

export const metadata: Metadata = {
  title: "OmniAI - One AI. Unlimited Possibilities.",
  description: "AI-powered platform for documents, websites, bots, chat, code generation, and more.",
  keywords: ["AI", "document humanizer", "website builder", "chatbot", "code generation", "OmniAI"],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <Providers>
          <AuthProvider>
            {children}
          </AuthProvider>
          <Toaster position="top-right" richColors />
        </Providers>
      </body>
    </html>
  );
}
