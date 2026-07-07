import { useMemo, useState } from "react";
import {
  CATALOG_SECTIONS,
  PROJECT_APPS,
  STATS,
  type CatalogItem,
  type CatalogSection,
} from "../projectCatalog";

function FieldList({ fields }: { fields: string[] }) {
  return (
    <ul className="mt-1 space-y-1">
      {fields.map((f) => (
        <li
          key={f}
          className="rounded-md border border-cosmic-100 bg-white px-2.5 py-1.5 text-xs text-slate-700"
        >
          {f}
        </li>
      ))}
    </ul>
  );
}

function CatalogCard({ item }: { item: CatalogItem }) {
  return (
    <article className="rounded-lg border border-cosmic-200/50 bg-white/90 p-3 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <h4 className="text-sm font-semibold text-cosmic-900">{item.name}</h4>
        <div className="flex flex-wrap gap-1">
          {item.plan ? (
            <span className="rounded-full bg-blue-50 px-2 py-0.5 text-[10px] font-semibold text-blue-700">
              {item.plan}
            </span>
          ) : null}
          {item.price ? (
            <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold text-emerald-700">
              {item.price}
            </span>
          ) : null}
        </div>
      </div>
      {item.route ? (
        <code className="mt-1 block text-[11px] text-cosmic-600">{item.route}</code>
      ) : null}
      <p className="mt-1.5 text-xs leading-relaxed text-slate-600">{item.purpose}</p>
      {item.fields?.length ? (
        <div className="mt-2">
          <p className="text-[10px] font-bold uppercase tracking-wide text-cosmic-700">
            Form fields
          </p>
          <FieldList fields={item.fields} />
        </div>
      ) : null}
      {item.api ? (
        <p className="mt-2 text-[10px] text-slate-500">
          <span className="font-bold text-cosmic-700">API:</span>{" "}
          <code className="text-[10px]">{item.api}</code>
        </p>
      ) : null}
    </article>
  );
}

function SectionBlock({
  section,
  defaultOpen,
}: {
  section: CatalogSection;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen ?? false);
  return (
    <section className="rounded-xl border border-cosmic-300/30 bg-white/80 shadow-sm">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left"
      >
        <div>
          <p className="text-sm font-bold text-cosmic-900">
            {section.emoji} {section.title}
            <span className="ml-2 text-xs font-normal text-slate-500">
              ({section.items.length})
            </span>
          </p>
          <p className="mt-0.5 text-xs text-slate-600">{section.description}</p>
        </div>
        <span className="text-cosmic-500">{open ? "▲" : "▼"}</span>
      </button>
      {open ? (
        <div className="grid gap-2 border-t border-cosmic-100 px-3 pb-3 pt-2 sm:grid-cols-2">
          {section.items.map((item) => (
            <CatalogCard key={item.name} item={item} />
          ))}
        </div>
      ) : null}
    </section>
  );
}

export function ProjectCatalog() {
  const [query, setQuery] = useState("");
  const [activeSection, setActiveSection] = useState<string>("all");

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return CATALOG_SECTIONS.map((section) => {
      if (activeSection !== "all" && section.id !== activeSection) return null;
      const items = section.items.filter((item) => {
        if (!q) return true;
        const hay = [
          item.name,
          item.route ?? "",
          item.purpose,
          item.api ?? "",
          item.price ?? "",
          ...(item.fields ?? []),
        ]
          .join(" ")
          .toLowerCase();
        return hay.includes(q);
      });
      if (!items.length) return null;
      return { ...section, items };
    }).filter(Boolean) as CatalogSection[];
  }, [query, activeSection]);

  const totalShown = filtered.reduce((n, s) => n + s.items.length, 0);

  return (
    <div className="mx-auto max-w-4xl px-3 pb-10">
      {/* Stats bar */}
      <div className="mb-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
        {[
          { label: "Mobile screens", value: STATS.mobileScreens },
          { label: "Catalog items", value: STATS.catalogItems },
          { label: "Apps / sites", value: STATS.apps },
          { label: "Paid products", value: STATS.paidProducts },
        ].map((s) => (
          <div
            key={s.label}
            className="rounded-lg border border-cosmic-200/60 bg-white/90 px-3 py-2 text-center"
          >
            <p className="text-lg font-bold text-cosmic-800">{s.value}+</p>
            <p className="text-[10px] uppercase tracking-wide text-slate-500">{s.label}</p>
          </div>
        ))}
      </div>

      {/* Apps to run */}
      <div className="mb-4 rounded-xl border border-cosmic-300/40 bg-white/95 p-4 shadow-sm">
        <h2 className="text-base font-bold text-cosmic-800">🚀 Kaise chalayein (local)</h2>
        <div className="mt-3 space-y-2">
          {PROJECT_APPS.map((app) => (
            <div
              key={app.name}
              className="rounded-lg border border-cosmic-100 bg-cosmic-50/40 px-3 py-2"
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="text-sm font-semibold text-slate-800">{app.name}</p>
                <span className="rounded bg-white px-2 py-0.5 text-[10px] font-mono text-cosmic-700">
                  :{app.port}
                </span>
              </div>
              <p className="text-xs text-slate-600">{app.purpose}</p>
              <code className="mt-1 block rounded bg-white px-2 py-1 text-[10px] text-slate-700">
                {app.run}
              </code>
            </div>
          ))}
        </div>
      </div>

      {/* Search & filter */}
      <div className="mb-4 rounded-xl border border-cosmic-300/40 bg-white/95 p-4 shadow-sm">
        <h2 className="text-base font-bold text-cosmic-800">
          📂 Pura Cosmic Lens Project — form catalog
        </h2>
        <p className="mt-1 text-xs text-slate-600">
          Har screen, form field, API aur paid product — searchable list mein.
          {totalShown < STATS.catalogItems ? ` Showing ${totalShown} matches.` : null}
        </p>
        <input
          type="search"
          placeholder="Search: love, vastu, payment, kundli…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="mt-3 w-full rounded-lg border border-cosmic-200 px-3 py-2 text-sm outline-none focus:border-cosmic-500"
        />
        <div className="mt-2 flex flex-wrap gap-1.5">
          <button
            type="button"
            onClick={() => setActiveSection("all")}
            className={`rounded-full px-2.5 py-1 text-[11px] font-semibold ${
              activeSection === "all" ? "bg-cosmic-600 text-white" : "bg-slate-100 text-slate-600"
            }`}
          >
            Sab
          </button>
          {CATALOG_SECTIONS.map((s) => (
            <button
              key={s.id}
              type="button"
              onClick={() => setActiveSection(s.id)}
              className={`rounded-full px-2.5 py-1 text-[11px] font-semibold ${
                activeSection === s.id ? "bg-cosmic-600 text-white" : "bg-slate-100 text-slate-600"
              }`}
            >
              {s.emoji} {s.title.split(" ")[0]}
            </button>
          ))}
        </div>
      </div>

      {/* Sections */}
      <div className="space-y-3">
        {filtered.length === 0 ? (
          <p className="text-center text-sm text-slate-500">Koi match nahi — search badlo.</p>
        ) : (
          filtered.map((section, i) => (
            <SectionBlock key={section.id} section={section} defaultOpen={i === 0 || !!query} />
          ))
        )}
      </div>
    </div>
  );
}
