function w() {}
const D = (t) => t;
function E(t, n) {
  for (const e in n) t[e] = n[e];
  return t;
}
function j(t) {
  return t();
}
function M() {
  return Object.create(null);
}
function q(t) {
  t.forEach(j);
}
function S(t) {
  return typeof t == "function";
}
function A(t, n) {
  return t != t
    ? n == n
    : t !== n || (t && typeof t == "object") || typeof t == "function";
}
let l;
function B(t, n) {
  return t === n
    ? !0
    : (l || (l = document.createElement("a")), (l.href = n), t === l.href);
}
function C(t) {
  return Object.keys(t).length === 0;
}
function y(t, ...n) {
  if (t == null) {
    for (const r of n) r(void 0);
    return w;
  }
  const e = t.subscribe(...n);
  return e.unsubscribe ? () => e.unsubscribe() : e;
}
function P(t) {
  let n;
  return y(t, (e) => (n = e))(), n;
}
function U(t, n, e) {
  t.$$.on_destroy.push(y(n, e));
}
function G(t, n, e, r) {
  if (t) {
    const o = x(t, n, e, r);
    return t[0](o);
  }
}
function x(t, n, e, r) {
  return t[1] && r ? E(e.ctx.slice(), t[1](r(n))) : e.ctx;
}
function H(t, n, e, r) {
  if (t[2] && r) {
    const o = t[2](r(e));
    if (n.dirty === void 0) return o;
    if (typeof o == "object") {
      const a = [],
        _ = Math.max(n.dirty.length, o.length);
      for (let u = 0; u < _; u += 1) a[u] = n.dirty[u] | o[u];
      return a;
    }
    return n.dirty | o;
  }
  return n.dirty;
}
function I(t, n, e, r, o, a) {
  if (o) {
    const _ = x(n, e, r, a);
    t.p(_, o);
  }
}
function J(t) {
  if (t.ctx.length > 32) {
    const n = [],
      e = t.ctx.length / 32;
    for (let r = 0; r < e; r++) n[r] = -1;
    return n;
  }
  return -1;
}
function K(t) {
  const n = {};
  for (const e in t) e[0] !== "$" && (n[e] = t[e]);
  return n;
}
function L(t, n) {
  const e = {};
  n = new Set(n);
  for (const r in t) !n.has(r) && r[0] !== "$" && (e[r] = t[r]);
  return e;
}
function N(t) {
  return t ?? "";
}
function Q(t) {
  const n = typeof t == "string" && t.match(/^\s*(-?[\d.]+)([^\s]*)\s*$/);
  return n ? [parseFloat(n[1]), n[2] || "px"] : [t, "px"];
}
let f;
function d(t) {
  f = t;
}
function g() {
  if (!f) throw new Error("Function called outside component initialization");
  return f;
}
function R(t) {
  g().$$.on_mount.push(t);
}
function T(t) {
  g().$$.after_update.push(t);
}
function V(t) {
  g().$$.on_destroy.push(t);
}
const i = [],
  b = [];
let c = [];
const m = [],
  k = Promise.resolve();
let p = !1;
function v() {
  p || ((p = !0), k.then(O));
}
function W() {
  return v(), k;
}
function F(t) {
  c.push(t);
}
const h = new Set();
let s = 0;
function O() {
  if (s !== 0) return;
  const t = f;
  do {
    try {
      for (; s < i.length; ) {
        const n = i[s];
        s++, d(n), z(n.$$);
      }
    } catch (n) {
      throw ((i.length = 0), (s = 0), n);
    }
    for (d(null), i.length = 0, s = 0; b.length; ) b.pop()();
    for (let n = 0; n < c.length; n += 1) {
      const e = c[n];
      h.has(e) || (h.add(e), e());
    }
    c.length = 0;
  } while (i.length);
  for (; m.length; ) m.pop()();
  (p = !1), h.clear(), d(t);
}
function z(t) {
  if (t.fragment !== null) {
    t.update(), q(t.before_update);
    const n = t.dirty;
    (t.dirty = [-1]),
      t.fragment && t.fragment.p(t.ctx, n),
      t.after_update.forEach(F);
  }
}
function X(t) {
  const n = [],
    e = [];
  c.forEach((r) => (t.indexOf(r) === -1 ? n.push(r) : e.push(r))),
    e.forEach((r) => r()),
    (c = n);
}
export {
  v as A,
  P as B,
  Q as C,
  V as D,
  N as E,
  B as F,
  T as a,
  b,
  G as c,
  E as d,
  H as e,
  L as f,
  J as g,
  K as h,
  U as i,
  S as j,
  F as k,
  D as l,
  M as m,
  w as n,
  R as o,
  O as p,
  C as q,
  q as r,
  A as s,
  W as t,
  I as u,
  X as v,
  f as w,
  d as x,
  j as y,
  i as z,
};
