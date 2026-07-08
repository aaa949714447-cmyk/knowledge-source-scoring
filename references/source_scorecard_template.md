# 知识来源评分表模板

```yaml
query: ""
retrieved_at: "YYYY-MM-DD"
candidate_sources:
  - source_url: ""
    source_title: ""
    source_type: "official_docs | paper | university | reputable_reference | engineering_blog | community_blog | qna | marketing | aggregator | unknown"
    publisher: ""
    author: ""
    published_or_updated_at: ""
    claim_supported: ""
    evidence_excerpt: ""
    scoring_breakdown:
      authority: 0
      traceability: 0
      technical_depth: 0
      freshness: 0
      cross_validation: 0
      bias_penalty: 0
    source_score: 0
    source_level: "A | B | C | D"
    image_inventory:
      total_images: 0
      skipped_images: []
      images_requiring_multimodal: []
    multimodal_usage:
      used: false
      model: ""
      reason: ""
    risk_notes: ""

cross_validation:
  matched_claims: []
  conflicts: []

decision:
  review_status: "auto_accepted | needs_review | rejected"
  reason: ""
  allowed_for_formal_kb: false
```
