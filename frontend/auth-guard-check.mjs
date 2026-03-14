import { resolveAuthRedirect } from "./src/router/index.js"

const case1 = resolveAuthRedirect({ path: "/jobs", fullPath: "/jobs", meta: { requiresAuth: true } }, false)
const case2 = resolveAuthRedirect({ path: "/jobs", fullPath: "/jobs", meta: { requiresAuth: true } }, true)
const case3 = resolveAuthRedirect({ path: "/login", fullPath: "/login", meta: {} }, true)

console.log("case1", JSON.stringify(case1))
console.log("case2", JSON.stringify(case2))
console.log("case3", JSON.stringify(case3))
