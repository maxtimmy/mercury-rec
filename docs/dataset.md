# Dataset and provenance

## Source

Primary dataset: **H&M Personalized Fashion Recommendations** (Kaggle). До загрузки зафиксировать ссылку на source, дату получения, условия использования, archive checksum и список файлов в versioned dataset manifest. Сырые данные и credentials не коммитятся в Git.

## Expected source files

| File | Role | Key fields |
|---|---|---|
| `transactions_train.csv` | purchase history | `t_dat`, `customer_id`, `article_id`, `price`, `sales_channel_id` |
| `customers.csv` | customer metadata | `customer_id`, optional demographic fields |
| `articles.csv` | item metadata | `article_id`, product/category fields |

Source schema must be verified from the downloaded artifact rather than assumed. The data adapter maps source names to the canonical contracts in [data-and-features.md](data-and-features.md).

## Manifest template

```yaml
dataset:
  name: hm-personalized-fashion-recommendations
  source_url: TBD
  retrieved_at_utc: TBD
  license_or_terms_url: TBD
  archive_sha256: TBD
  raw_schema_version: 1
  adapter_version: TBD
  timezone: UTC
```

## Data preparation rules

- Keep raw files immutable; produce normalized Parquet tables in a separate, ignored data directory.
- Parse `t_dat` with an explicit timezone convention and convert all event timestamps to UTC.
- Do not infer unavailable fields (for example country) from a dataset that does not provide them.
- Maintain a data-quality report: row counts, null rates, ID uniqueness, timestamp range, price summary and referential-integrity failures.
- Document any filtering such as unavailable catalog items, duplicate transactions or a minimum user/item activity threshold.

## Reproducible temporal split

The first implementation must store exact cutoff timestamps, horizons and population filters in `configs/splits/*.yaml`. The illustrative Jan–May/June split in the README is not binding; actual boundaries depend on the source time range and must remain untouched once reported for a benchmark.
