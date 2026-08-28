import type { LegalBlock, LegalDoc } from "./legalPolicies";

function Block({ block }: { block: LegalBlock }) {
  if (block.type === "p") {
    return <p className="legal-p">{block.text}</p>;
  }
  if (block.type === "bullet") {
    return (
      <li className="legal-li">
        {block.text}
      </li>
    );
  }
  const tone = block.tone ?? "info";
  return (
    <div className={`legal-callout legal-callout-${tone}`}>
      {block.text}
    </div>
  );
}

export function LegalPolicyView({
  doc,
  lastUpdated,
}: {
  doc: LegalDoc;
  lastUpdated: string;
}) {
  return (
    <article className="legal-doc">
      <header className="legal-doc-head">
        <h1>{doc.title}</h1>
        {doc.subtitle ? <p className="legal-subtitle">{doc.subtitle}</p> : null}
        <p className="legal-meta">Last updated: {lastUpdated}</p>
      </header>
      {doc.intro ? <p className="legal-intro">{doc.intro}</p> : null}
      {doc.topCallout ? (
        <div className={`legal-callout legal-callout-${doc.topCallout.tone ?? "info"}`}>
          {doc.topCallout.text}
        </div>
      ) : null}
      {doc.sections.map((sec) => (
        <section key={sec.title} className="legal-section">
          <h2>{sec.title}</h2>
          {sec.blocks.some((b) => b.type === "bullet") ? (
            <ul className="legal-ul">
              {sec.blocks.map((block, i) =>
                block.type === "bullet" ? <Block key={i} block={block} /> : null,
              )}
            </ul>
          ) : null}
          {sec.blocks.map((block, i) =>
            block.type !== "bullet" ? <Block key={i} block={block} /> : null,
          )}
        </section>
      ))}
    </article>
  );
}
