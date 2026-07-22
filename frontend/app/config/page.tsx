import ConfigEditor from "@/components/ConfigEditor";

export const metadata = {
  title: "Config – Contractor Bot",
};

export default function ConfigPage() {
  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold text-gray-900">Business config</h1>
      <ConfigEditor />
    </div>
  );
}
