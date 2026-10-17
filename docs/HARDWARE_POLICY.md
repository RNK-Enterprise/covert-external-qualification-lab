# Hardware Policy

Q0 records static capacity/runtime facts only: no stress run, driver change, package install, storage cleanup, privilege elevation, or whole-disk scan.

Phoenix reported PRIMARY CPU/RAM NODE: Ryzen 7 5825U, 27 GB usable RAM, integrated AMD Barcelo/shared VRAM. Atlas reported NVIDIA PARTIAL-OFFLOAD/COMPATIBILITY NODE: i5-10300H, 31 GB RAM, GTX 1650 Mobile 4 GB; CUDA toolkit not previously observed. Reverify both. Neither is high-end GPU.

Heavy tiers: CPU/RAM HEAVY, 16 GB VRAM, 24 GB VRAM, 32+ GB VRAM. Pack contains specs/batteries/evidence/cleanup, not weights. Unknown resource needs fail admission.