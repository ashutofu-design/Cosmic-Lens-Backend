import { PLAY_STORE_URL } from "./constants";

export function GooglePlayBadge({
  large = false,
  header = false,
}: {
  large?: boolean;
  header?: boolean;
}) {
  return (
    <a
      className={`site-play${large ? " site-play-lg" : ""}${header ? " site-play-header" : ""}`}
      href={PLAY_STORE_URL}
      target="_blank"
      rel="noopener noreferrer"
      aria-label="Get Cosmic Lens on Google Play"
    >
      <svg width="22" height="24" viewBox="0 0 22 24" fill="none" aria-hidden>
        <path d="M1.2 1.6c-.7.5-1.2 1.4-1.2 2.5v15.8c0 1.1.5 2 1.2 2.5l10.2-10.4L1.2 1.6z" fill="#4285F4" />
        <path d="M15.4 12.8l-3.9-3.9L1.2 1.6c.3-.2.6-.4 1-.4.5 0 1.1.2 2 .7l12.4 7.1-1.2 3.8z" fill="#EA4335" />
        <path d="M15.4 11.2l1.2 3.8-12.4 7.1c-.9.5-1.5.7-2 .7-.4 0-.7-.1-1-.4l10.3-10.4 3.9-3.8z" fill="#34A853" />
        <path d="M21.2 12c0 .8-.4 1.5-1.2 2L16.6 16l-1.2-3.8 1.2-3.8 3.4 2c.8.5 1.2 1.2 1.2 2z" fill="#FBBC04" />
      </svg>
      <span>
        <small>GET IT ON</small>
        <strong>Google Play</strong>
      </span>
      {header ? <i aria-hidden>↗</i> : null}
    </a>
  );
}
