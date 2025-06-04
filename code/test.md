
### 🔹 `client_id`
- Your **App’s Client ID**, found in the **Keys and Tokens** section of your app dashboard.
- Required for identifying your app during the authorization flow.

---

### 🔹 `redirect_uri`
- The **Callback URL** Twitter will redirect to after the user logs in.
- Must **match exactly** what’s listed in your app settings (e.g., `http://localhost:8000/callback`)
- During development, use a local server or a tool like [ngrok](https://ngrok.com/) to test this.

---

### 🔹 `scope`
- List of **permissions** you’re requesting from the user.
- Examples:
  - `"tweet.read"` – read tweets
  - `"tweet.write"` – post tweets
  - `"users.read"` – get user profile info
  - `"offline.access"` – allows you to refresh the token later

✅ **Required if you want to post tweets:**  
```python
scope=["tweet.write", "tweet.read", "users.read", "offline.access"]
