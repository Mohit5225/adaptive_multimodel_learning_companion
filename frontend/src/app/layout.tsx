import { Inter, JetBrains_Mono } from "next/font/google";
import { ClerkProvider } from "@clerk/nextjs";
import "./globals.css";
import { Outfit, Plus_Jakarta_Sans } from "next/font/google";
import "./globals.css";
import { dark } from "@clerk/themes";
const outfit = Outfit({ subsets: ["latin"], variable: "--font-outfit" });
const jakarta = Plus_Jakarta_Sans({ subsets: ["latin"], variable: "--font-jakarta" }); import { Metadata } from "next";

const inter = Inter({ subsets: ["latin"], variable: "--font-sans" });
const jetbrainsMono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono" });

export const metadata: Metadata = {
  title: "Socratic Visuals",
  description: "AI-powered educational math video creation with Manim",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <ClerkProvider appearance={{
      baseTheme: dark,
      variables: {
        colorPrimary: '#FFFFFF', // Pure White
        colorBackground: 'transparent', // Transparent for glass effect
        colorText: '#FFFFFF',
        colorTextSecondary: '#E2E8F0', // Light Gray (High Contrast)
        fontFamily: outfit.style.fontFamily,
        borderRadius: "0.5rem", // Slight rounded for ergonomics
        spacingUnit: "1.5rem", // Hyper-Spacious
      },
      elements: {
        card: "bg-transparent shadow-none p-0", // Remove default card styling to use our wrapper
        navbar: "hidden",
        headerTitle: "hidden", // We use our own custom header
        headerSubtitle: "hidden", // We use our own custom header
        formFieldInput: "bg-white/5 border-2 border-white/10 hover:border-cyan-500 focus:border-cyan-500 transition-colors h-16 text-xl px-6 rounded-xl font-bold",
        formFieldLabel: "text-gray-300 text-sm uppercase tracking-widest mb-3 font-bold",
        formButtonPrimary: "jelly-button bg-white text-black h-16 text-xl font-bold hover:bg-gray-200 transition-all rounded-xl",
        socialButtonsBlockButton: "h-16 bg-white/5 border-2 border-white/10 hover:bg-white/10 transition-colors rounded-xl",
        socialButtonsBlockButtonText: "text-white font-bold text-lg",
        footerActionLink: "text-cyan-400 hover:text-cyan-300 font-bold text-lg",
        dividerLine: "bg-white/10",
        dividerText: "text-gray-400 font-bold",
      }
    }}>
      <html lang="en">
        <body className={`${outfit.variable} ${jakarta.variable} font-sans antialiased selection:bg-cyan-500 selection:text-black bg-void text-white`}>

          {/* Subtle Grid Background for Structure */}
          <div className="fixed inset-0 pointer-events-none z-[-1] opacity-[0.03]"
            style={{
              backgroundImage: 'linear-gradient(#ffffff 1px, transparent 1px), linear-gradient(90deg, #ffffff 1px, transparent 1px)',
              backgroundSize: '50px 50px'
            }}
          />

          {children}
        </body>
      </html>
    </ClerkProvider >
  );
}
