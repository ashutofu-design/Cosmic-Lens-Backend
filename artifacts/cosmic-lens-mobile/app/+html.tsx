import { ScrollViewStyleReset } from "expo-router/html";
import type { PropsWithChildren } from "react";

/** Web shell. Height is set via script (not <style>) so Windows lightningcss is not triggered. */
export default function Root({ children }: PropsWithChildren) {
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta httpEquiv="X-UA-Compatible" content="IE=edge" />
        <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no" />
        <ScrollViewStyleReset />
      </head>
      <body>
        {children}
        <script
          dangerouslySetInnerHTML={{
            __html:
              '(function(){function s(el){if(!el||!el.style)return;el.style.width="100%";el.style.height="100%";el.style.minHeight="100vh";el.style.margin="0";el.style.padding="0";}s(document.documentElement);s(document.body);s(document.getElementById("root"));if(document.body){document.body.style.backgroundColor="#0B1220";}var r=document.getElementById("root");if(r){r.style.display="flex";r.style.flexDirection="column";}})();',
          }}
        />
      </body>
    </html>
  );
}
