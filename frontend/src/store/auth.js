import { defineStore } from "pinia"

export const useAuthStore = defineStore("auth", {
  state: () => ({
    accessToken: localStorage.getItem("accessToken") || "",
    refreshToken: localStorage.getItem("refreshToken") || ""
  }),
  actions: {
    setTokens({ access, refresh }) {
      this.accessToken = access
      this.refreshToken = refresh
      localStorage.setItem("accessToken", access)
      localStorage.setItem("refreshToken", refresh)
    },
    logout() {
      this.accessToken = ""
      this.refreshToken = ""
      localStorage.removeItem("accessToken")
      localStorage.removeItem("refreshToken")
    }
  }
})
