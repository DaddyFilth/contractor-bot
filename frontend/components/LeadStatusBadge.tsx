import type { Lead } from "@/lib/supabase";

type Props = {
  status: Lead["status"];
};

const styles: Record<Lead["status"], string> = {
  open: "bg-yellow-100 text-yellow-800",
  responded: "bg-blue-100 text-blue-800",
  closed: "bg-green-100 text-green-800",
};

export default function LeadStatusBadge({ status }: Props) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${styles[status]}`}
    >
      {status}
    </span>
  );
}
