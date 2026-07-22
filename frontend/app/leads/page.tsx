import LeadsTable from "@/components/LeadsTable";

export const metadata = {
  title: "Leads – Contractor Bot",
};

export default function LeadsPage() {
  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold text-gray-900">Leads</h1>
      <LeadsTable />
    </div>
  );
}
