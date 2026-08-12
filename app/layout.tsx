import type { Metadata } from "next";
import "./styles.css";

export const metadata: Metadata = {
  title: "Contractor Bot",
  description: "Contractor lead and call dashboard"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
