terraform {
  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
  }
}

locals {
  # All 5 domains require DNSSEC
  all_domains = toset([
    "cortexpersist.org",
    "cortexpersist.dev",
    "cortexpersist.com",
    "babylon60.com",
    "agents.archi"
  ])

  # Only parked domains require strict null records to prevent spoofing
  parked_domains = toset([
    "cortexpersist.org",
    "babylon60.com",
    "agents.archi"
  ])
}

variable "zone_ids" {
  type        = map(string)
  description = "Map of domains to Cloudflare Zone IDs"
}

# Enforce DNSSEC for all 5 domains
resource "cloudflare_zone_dnssec" "strict_dnssec" {
  for_each = local.all_domains
  zone_id  = var.zone_ids[each.key]
}

# Strict SPF (Reject all) for parked domains
resource "cloudflare_record" "spf_strict" {
  for_each = local.parked_domains
  zone_id  = var.zone_ids[each.key]
  name     = "@"
  type     = "TXT"
  content  = "v=spf1 -all"
  ttl      = 3600
}

# Strict DMARC (Reject) for parked domains
resource "cloudflare_record" "dmarc_strict" {
  for_each = local.parked_domains
  zone_id  = var.zone_ids[each.key]
  name     = "_dmarc"
  type     = "TXT"
  content  = "v=DMARC1; p=reject; sp=reject; adkim=s; aspf=s;"
  ttl      = 3600
}

# Null DKIM for parked domains
resource "cloudflare_record" "dkim_null" {
  for_each = local.parked_domains
  zone_id  = var.zone_ids[each.key]
  name     = "*._domainkey"
  type     = "TXT"
  content  = "v=DKIM1; p="
  ttl      = 3600
}
