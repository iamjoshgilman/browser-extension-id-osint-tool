# Browser Extension OSINT Tool

A comprehensive web-based tool for investigating browser extensions across Chrome Web Store, Firefox Add-ons, and Microsoft Edge Add-ons. Search and analyze extensions to gather intelligence about publishers, user counts, permissions, and cross-platform availability.

## 🎯 Purpose

Browser extensions have significant access to user data and browsing activity, yet there's limited tooling for security researchers and IT administrators to investigate them efficiently. This tool was created to:

- **Enable Security Research**: Quickly identify extensions across multiple stores and analyze their metadata
- **Support Threat Hunting**: Investigate suspicious extensions by checking their presence and details across platforms
- **Facilitate Compliance Audits**: Help organizations audit browser extensions used within their environment
- **Provide Transparency**: Make extension information more accessible for privacy-conscious users

## 🔍 Features

### Multi-Store Search
- **Unified Search Interface**: Search across Chrome, Firefox, and Edge stores simultaneously
- **Single & Bulk Search**: Look up individual extensions or process lists of extension IDs
- **Cross-Platform Analysis**: See how the same extension appears across different stores

### Intelligent Data Collection
- **Smart Caching**: Reduces redundant requests and improves response times
- **Comprehensive Metadata**: Extracts extension names, publishers, user counts, ratings, versions, and descriptions
- **Not Found Detection**: Clearly indicates when an extension doesn't exist in a particular store

### Modern Architecture
- **RESTful API**: Clean API design for easy integration with other tools
- **Responsive Web Interface**: Works seamlessly on desktop and mobile devices
- **Rate Limiting**: Responsible scraping with configurable delays and limits
- **Docker Deployment**: Containerized for easy hosting and scalability

## 🚀 Use Cases

### Security Operations
- Investigate potentially malicious extensions reported by users
- Track extension proliferation across different browser stores
- Identify publisher patterns and naming inconsistencies

### IT Administration
- Audit extensions installed in corporate environments
- Verify extension authenticity before whitelisting
- Monitor for unauthorized or risky extensions

### Privacy Research
- Analyze extension permissions and data access
- Track user adoption across platforms
- Research extension ecosystem trends

## 🛡️ Ethical Considerations

This tool is designed for legitimate security research and IT administration purposes. Users should:

- Respect the terms of service of browser extension stores
- Use rate limiting to avoid overloading services
- Only investigate extensions for authorized purposes
- Report security issues through appropriate channels

## 🔧 Technical Stack

- **Backend**: Python Flask with BeautifulSoup for web scraping
- **Frontend**: Vanilla JavaScript with modern CSS (Catppuccin theme)
- **Database**: SQLite for caching and search history
- **Deployment**: Docker with nginx reverse proxy
- **Rate Limiting**: Flask-Limiter for responsible API usage

## 📊 Data Points Collected

For each extension, the tool attempts to gather:
- Extension name and ID
- Publisher information
- User count/install base
- Rating and review count
- Current version
- Description
- Store URL
- Last updated date (when available)

## ⚖️ Legal Notice

This tool is provided for educational and research purposes. Users are responsible for complying with all applicable laws and terms of service. The tool does not bypass any security measures and only accesses publicly available information.

## 🙏 Acknowledgments

- Built with Flask and BeautifulSoup
- UI theme inspired by Catppuccin Frappé
- Created to support the security research community

---

## 🐛 Known Bugs

- Edge scraper returning "unknown" results
- Some information not getting captured such as ratings

---

* Vibe Codded With Love 🖤 *
