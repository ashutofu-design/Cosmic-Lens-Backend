import React from "react";
import { Bullet, Callout, P, Section } from "@/components/LegalScreen";
import type { LegalDoc } from "@/lib/legalPolicies";

/** Renders policy sections only (no outer LegalScreen header). */
export function LegalPolicyBody({ doc }: { doc: LegalDoc }) {
  return (
    <>
      {doc.intro ? <P>{doc.intro}</P> : null}
      {doc.topCallout ? (
        <Callout tone={doc.topCallout.tone ?? "info"}>{doc.topCallout.text}</Callout>
      ) : null}
      {doc.sections.map((sec) => (
        <Section key={sec.title} title={sec.title}>
          {sec.blocks.map((block, i) => {
            if (block.type === "p") return <P key={i}>{block.text}</P>;
            if (block.type === "bullet") return <Bullet key={i}>{block.text}</Bullet>;
            return (
              <Callout key={i} tone={block.tone ?? "info"}>
                {block.text}
              </Callout>
            );
          })}
        </Section>
      ))}
    </>
  );
}
