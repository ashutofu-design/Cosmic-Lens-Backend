type IgAutomationPreviewProps = {
  videoNumber: string;
  triggerText: string;
  replyText: string;
};

export function IgAutomationPreview({
  videoNumber,
  triggerText,
  replyText,
}: IgAutomationPreviewProps) {
  const vn = videoNumber.trim();
  const trigger = triggerText.trim();
  const reply = replyText.trim();

  return (
    <div className="ig-auto-preview">
      <div className="ig-auto-preview-head">
        Instagram DM preview
        <span>Trigger → auto-reply</span>
      </div>
      <div className="ig-auto-preview-body">
        <div className="ig-auto-preview-meta">
          {vn ? `Reel / video #${vn}` : "Set video number"}
          {" · "}
          Exact word match (case-insensitive)
        </div>
        <div className="ig-auto-bubble ig-auto-bubble-user">
          <div className="ig-auto-bubble-label">USER DM</div>
          {trigger ? trigger : (
            <span className="ig-auto-bubble-placeholder">Sun in 11th house</span>
          )}
        </div>
        <div className="ig-auto-bubble ig-auto-bubble-bot">
          <div className="ig-auto-bubble-label">AUTO-REPLY (saved message)</div>
          {reply ? reply : (
            <span className="ig-auto-bubble-placeholder">
              Yahan jo message save karenge — wahi app user ko dikhega.
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
