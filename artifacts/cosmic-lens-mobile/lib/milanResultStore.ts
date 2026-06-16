let _result: any = null;
let _openProOnReturn = false;

export const MilanResultStore = {
  set(r: any) { _result = r; },
  get() { return _result; },
  clear() { _result = null; },
  requestProOnReturn() { _openProOnReturn = true; },
  consumeProRequest() {
    const v = _openProOnReturn;
    _openProOnReturn = false;
    return v;
  },
};
