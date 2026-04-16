let _result: any = null;

export const MilanResultStore = {
  set(r: any) { _result = r; },
  get() { return _result; },
  clear() { _result = null; },
};
