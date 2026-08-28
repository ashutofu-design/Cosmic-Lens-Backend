/** Normalized pathname for public vs admin routing. */
export function routePath(): string {
  let path = window.location.pathname || "/";
  if (path.endsWith("/index.html")) {
    path = path.slice(0, -"/index.html".length) || "/";
  }
  path = path.replace(/\/+$/, "");
  return path || "/";
}

export function isAdminRoute(path = routePath()): boolean {
  return path === "/admin" || path.startsWith("/admin/");
}
