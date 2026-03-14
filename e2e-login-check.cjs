const { chromium } = require("playwright")

async function main() {
  const browser = await chromium.launch({ headless: true })
  const page = await browser.newPage()
  await page.goto("http://localhost:5173/jobs")
  await page.waitForTimeout(1200)
  const beforeLoginUrl = page.url()
  await page.locator("input[name='username']").fill("demo_user")
  await page.locator("input[name='password']").fill("demo123456")
  await page.getByTestId("login-submit").click()
  await page.waitForTimeout(1800)
  const afterLoginUrl = page.url()
  console.log(`before_login_url=${beforeLoginUrl}`)
  console.log(`after_login_url=${afterLoginUrl}`)
  await browser.close()
}

main()
