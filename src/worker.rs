#[derive(Debug, Clone, PartialEq, Eq)]
struct ParsedUrl {
    scheme: String,
    host_port: String,
    path: String,
}

pub fn enforce_single_inference_boundary(base: &str, endpoint: &str) -> crate::Result<()> {
    let base = parse_url(base)?;
    let endpoint = parse_url(endpoint)?;
    if base.scheme != endpoint.scheme || base.host_port != endpoint.host_port {
        return Err("endpoint is outside declared inference boundary origin".into());
    }
    if !endpoint.path.starts_with(&base.path) {
        return Err("endpoint path is outside declared boundary path".into());
    }
    Ok(())
}

fn parse_url(url: &str) -> crate::Result<ParsedUrl> {
    let (scheme, rest) = url.split_once("://").ok_or("URL must include scheme")?;
    let (host_port, path) = match rest.split_once('/') {
        Some((h, p)) => (h, format!("/{p}")),
        None => (rest, "/".to_string()),
    };
    if scheme.is_empty() || host_port.is_empty() {
        return Err("URL scheme and host are required".into());
    }
    Ok(ParsedUrl {
        scheme: scheme.to_string(),
        host_port: host_port.to_string(),
        path,
    })
}
