# X01 ATT&CK thật — nghiên cứu compatibility

Ngày kiểm: 11/11/2026 (Asia/Saigon). Source chỉ đọc: `cti-x01-attack-offline`, branch `feat/x01-attack-offline-20261111`, HEAD `4e894c37df3ad53c16022909ae6df113dd89aa04`; `git status --short` trước nghiên cứu không có output. Không sửa source, không chạy loader/test sản phẩm, cài package, model, lab hay dịch vụ mạng CTI.

## Kết luận

**Điều chỉnh nhỏ nhất loader stdlib hiện có để nhận `SnapshotPin(kind="official")` và bundle MITRE nguyên bytes; giữ synthetic như cũ.** Pin phải chứa release/tag/commit/URL/hash thật dưới đây; loader chỉ đọc tệp local đã cấp, tuyệt đối không tải khi lookup. Không dùng `stix2` trong lát cắt này: MITRE có minh họa `MemoryStore`, nhưng dependency mới không cần cho exact-ID lookup, lifecycle và parent graph đã có.

| Ai/cách đã làm | Nguồn kiểm chứng | Dùng lại được | Hạn chế / quyết định |
|---|---|---|---|
| MITRE ATT&CK — collection STIX 2.1 versioned | [index](https://github.com/mitre-attack/attack-stix-data/blob/master/index.md), [USAGE](https://github.com/mitre-attack/attack-stix-data/blob/master/USAGE.md) | `enterprise-attack-20.1.json`, bản local versioned, policy lọc revoked/deprecated | **Chọn** snapshot local có pin; `master`/tệp không version là mutable, không làm pin |
| `stix2` `MemoryStore` | [USAGE](https://github.com/mitre-attack/attack-stix-data/blob/master/USAGE.md) | Mẫu truy vấn STIX đầy đủ hơn khi C4/RAG cần | Thêm package/SBOM/API/kiểm tương thích; không cài/chạy |
| Loader restricted stdlib Phong Hỏa | `attack_catalog.py` tại SHA source nêu trên | strict JSON, bound 64 MiB, hash exact, index immutable, lifecycle/graph | Hiện chỉ nhận synthetic provenance, nên không tương thích official bundle |

## Pin đã quan sát

MITRE index liệt kê Enterprise ATT&CK **v20.1**, ngày 05/11/2026. GitHub REST xác nhận annotated tag `v20.1` object `fe094cfc533102f8eed3acefd89bb38a96fdf2c1` trỏ commit `f59b03ecf828579d5f9e93683ce25b7e2e5fd9d7`. Tệp tại commit: `enterprise-attack/enterprise-attack-20.1.json`; bytes tải nguyên trạng: **55,277,605**, SHA-256 **`539a843a7b53ed9749740b2123dddae3726b1a4831841c32aca740b011b910b5`**.

Manifest, URL bất biến, cách áp giới hạn download và hash script nằm tại `x01-attack-real-research-evidence/manifest.md`. License MITRE tại cùng commit cho phép dùng nghiên cứu/phát triển/thương mại với điều kiện tái tạo copyright designation và license trong mọi bản sao. Phải giữ LICENSE trong artifact/fixture distribution; `NOTICE` file riêng chưa xác minh được và không được bịa.

## Inventory thật (không phải test compatibility)

Script stdlib chỉ đọc `inventory_snapshot.py` đã chạy exit 0. Bundle có 26,699 object: 867 `attack-pattern` Enterprise; 706 active, 149 revoked, 12 deprecated; 497 sub-technique, 479 active. Có 481 cạnh `subtechnique-of` active, mọi active sub-technique có cạnh active và mọi target là parent Enterprise theo phép đếm script. Không thấy duplicate Enterprise STIX ID/external ID, và không có pattern thiếu/nhân `mitre-attack` external ID trong snapshot này.

Điểm khác policy hiện tại: root bundle không có `x_phonghoa_provenance`; pin official bị reject trước I/O; loader đòi provenance synthetic. Đây là blocker đúng cần sửa, không được nhét provenance Phong Hỏa vào bytes MITRE hoặc đổi `kind` thành synthetic.

Inventory không chứng minh loader pass: nó không gọi `load_catalog`, không kiểm error taxonomy, không kiểm semantic TTP; chỉ cho biết dữ liệu có dạng/độ lớn thật để viết fixture và test sau.

## Policy đề xuất

- Official pin bắt buộc: `kind="official"`, provenance `"mitre-attack-stix-data"`, version `"20.1"`, SHA-256 bytes, immutable `source_url`, `release_tag="v20.1"`, commit 40 hex. Synthetic giữ rule metadata MITRE đều `None`.
- Root bundle official không yêu cầu/không đọc `x_phonghoa_provenance`; synthetic vẫn phải có provenance root chính xác. Hai nhánh được chọn theo pin đã validate, không theo trường trong dữ liệu.
- Giữ strict JSON, 64 MiB và fail-closed. Snapshot này 55.28 MB nên hợp limit; nếu bản sau lớn hơn, fail `snapshot_too_large` và thay limit chỉ qua quyết định riêng có benchmark bộ nhớ.
- Không bỏ record khó: lifecycle `revoked`/`x_mitre_deprecated` vẫn index để lookup trả `inactive`; lookup chỉ `active` khi cả hai false. `semantic_status="unverified"` và `operational_draft_eligible=false` giữ nguyên.
- Canonical version/duplicate/parent policy hiện tại phải còn áp dụng; inventory snapshot không có duplicate, vì vậy cần fixture mutation riêng để test các nhánh này.

## Chưa xác minh

Không chạy loader sửa đổi hay product compatibility, chưa xác minh chữ ký cryptographic của tag ngoài GitHub REST, và chưa xác minh mọi trường ATT&CK/STIX ngoài subset loader. Bản sao LICENSE nguyên văn được giữ trong evidence. C4/RAG, semantic TTP, adapter, model/corpus, W05, OpenCTI, UI, lab và production đều ngoài scope.
