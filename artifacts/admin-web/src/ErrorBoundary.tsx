import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  error: Error | null;
  info: string;
}

/**
 * Catches render crashes and shows the real error on screen instead of a
 * blank white page — critical for debugging on mobile where devtools are
 * hard to reach.
 */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null, info: "" };

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    this.setState({ info: info.componentStack || "" });
    // eslint-disable-next-line no-console
    console.error("Admin panel crash:", error, info);
  }

  render() {
    if (this.state.error) {
      return (
        <div
          style={{
            padding: 24,
            fontFamily: "monospace",
            color: "#fecaca",
            background: "#450a0a",
            minHeight: "100vh",
          }}
        >
          <h2 style={{ color: "#fff" }}>Admin panel crashed</h2>
          <p>Screenshot this and send it to the developer:</p>
          <pre
            style={{
              whiteSpace: "pre-wrap",
              wordBreak: "break-word",
              background: "rgba(0,0,0,0.4)",
              padding: 12,
              borderRadius: 8,
            }}
          >
            {String(this.state.error?.stack || this.state.error)}
            {"\n\n"}
            {this.state.info}
          </pre>
          <button
            type="button"
            onClick={() => window.location.reload()}
            style={{ padding: "10px 16px", fontSize: 16 }}
          >
            Reload
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
