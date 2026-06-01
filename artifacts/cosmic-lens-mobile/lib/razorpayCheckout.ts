export type RazorpayCheckoutOpts = {
  keyId: string;
  orderId: string;
  amountPaise: number;
  title?: string;
  description?: string;
  customerName?: string;
  customerEmail?: string;
  customerPhone?: string;
  themeColor?: string;
};

export function buildRazorpayCheckoutHtml(opts: RazorpayCheckoutOpts): string {
  const title = opts.title || "Cosmic Lens";
  const description = opts.description || "Secure payment";
  const theme = opts.themeColor || "#7C3AED";
  return `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
  <style>body{margin:0;background:#0c0818;color:#fff;font-family:sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh}</style>
</head>
<body>
  <p>Opening Razorpay…</p>
  <script>
    function post(msg){ try { window.ReactNativeWebView && window.ReactNativeWebView.postMessage(JSON.stringify(msg)); } catch(e){} }
    var options = {
      key: ${JSON.stringify(opts.keyId)},
      amount: ${opts.amountPaise},
      currency: "INR",
      name: ${JSON.stringify(title)},
      description: ${JSON.stringify(description)},
      order_id: ${JSON.stringify(opts.orderId)},
      prefill: {
        name: ${JSON.stringify(opts.customerName || "User")},
        email: ${JSON.stringify(opts.customerEmail || "")},
        contact: ${JSON.stringify(opts.customerPhone || "")}
      },
      theme: { color: ${JSON.stringify(theme)} },
      handler: function (response) {
        post({ status: "success", payment_id: response.razorpay_payment_id, order_id: response.razorpay_order_id });
      },
      modal: {
        ondismiss: function () { post({ status: "dismissed" }); }
      }
    };
    var rzp = new Razorpay(options);
    rzp.on("payment.failed", function (resp) {
      post({ status: "failed", error: (resp.error && resp.error.description) || "Payment failed" });
    });
    rzp.open();
  </script>
</body>
</html>`;
}

declare global {
  interface Window {
    Razorpay?: new (options: Record<string, unknown>) => {
      open: () => void;
      on: (event: string, cb: (resp: unknown) => void) => void;
    };
  }
}

export async function openRazorpayCheckoutWeb(
  opts: RazorpayCheckoutOpts,
  onSuccess: () => void,
  onDismiss: () => void,
): Promise<void> {
  if (typeof window === "undefined") return;

  await new Promise<void>((resolve, reject) => {
    if (window.Razorpay) {
      resolve();
      return;
    }
    const existing = document.getElementById("razorpay-sdk-script");
    if (existing) {
      existing.addEventListener("load", () => resolve());
      existing.addEventListener("error", () => reject(new Error("Razorpay SDK load failed")));
      return;
    }
    const s = document.createElement("script");
    s.id = "razorpay-sdk-script";
    s.src = "https://checkout.razorpay.com/v1/checkout.js";
    s.async = true;
    s.onload = () => resolve();
    s.onerror = () => reject(new Error("Razorpay SDK load failed"));
    document.head.appendChild(s);
  });

  const Razorpay = window.Razorpay;
  if (!Razorpay) throw new Error("Razorpay SDK unavailable");

  const rzp = new Razorpay({
    key: opts.keyId,
    amount: opts.amountPaise,
    currency: "INR",
    name: opts.title || "Cosmic Lens",
    description: opts.description || "Secure payment",
    order_id: opts.orderId,
    prefill: {
      name: opts.customerName || "User",
      email: opts.customerEmail || "",
      contact: opts.customerPhone || "",
    },
    theme: { color: opts.themeColor || "#7C3AED" },
    handler: () => onSuccess(),
    modal: { ondismiss: () => onDismiss() },
  });
  rzp.on("payment.failed", () => onDismiss());
  rzp.open();
}
