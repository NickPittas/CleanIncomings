# SMB/NAS Performance Optimization Guide 🌐

## 🚀 **Core Strategy: Native Windows Commands for Optimal 10GbE Throughput** ⚡

**Primary Approach:** Utilize native Windows commands (`robocopy`/`xcopy`) for file operations to leverage full 10GbE network speeds, bypassing potential Python overhead for large file transfers over SMB.

### **🔥 Native Command Performance Advantages** 🚀
```
Primary:   ROBOCOPY with /J /MT:32 (unbuffered I/O + 32 threads for maximum throughput)
Fallback:  XCOPY with /Y /H (provides a balance of speed and compatibility)
Emergency: Python's `shutil.copy2()` (ensures operation completion if native commands fail, albeit at slower speeds)
```
**Benefit**: **Directly leverages Windows SMB client optimizations** - aims for native Windows Explorer-level performance.

### **Why Native Commands Can Be Significantly Faster for Network Transfers** 💡
- **Direct Windows SMB Client Access**: Reduces overhead from Python's file handling layers.
- **Kernel-Level Optimizations**: Benefits from the same efficiencies as Windows Explorer.
- **SMB3+ Protocol Features**: Can utilize advanced SMB features like multichannel, RDMA (if available), and better caching.
- **Optimized I/O**: Unbuffered I/O (`/J` in Robocopy) can be beneficial for large sequential transfers over a network by reducing cache contention.
- **OS-Level Multithreading**: Robocopy's `/MT` allows for true parallel transfers, which can saturate high-bandwidth links.

### **Illustrative Speed Comparison on a 10GbE Network** 📊
| Method                 | Potential Speed on 10GbE | Performance Tier |
|------------------------|--------------------------|------------------|
| **🚀 Robocopy /J /MT:32** | **~700-1200 MB/s (5.6-9.6 Gbps)** | **✅ MAXIMUM**   |
| **⚡ Xcopy /Y /H**       | **~400-800 MB/s (3.2-6.4 Gbps)**  | **✅ EXCELLENT** |
| Python `shutil.copy2`  | **~50-250 MB/s (0.4-2.0 Gbps)**   | **❌ BASELINE**  |
*(Actual speeds depend heavily on server load, client load, network conditions, and storage subsystem performance at both ends.)*

## 🎯 **Robocopy: Aggressive Settings for Speed**

```cmd
robocopy "source_dir" "dest_dir" "filename" /J /MT:32 /NFL /NDL /NP /R:0 /W:1 /COPY:DAT /DCOPY:T
```

**Key Flag Explanations:**
- `"source_dir" "dest_dir" "filename"`: Ensure paths and filename are correctly quoted, especially if they contain spaces.
- `/J`: **Unbuffered I/O**. Beneficial for large file transfers, reduces system cache overhead.
- `/MT:32`: **32 parallel threads**. Helps saturate high-bandwidth connections. Adjust based on core count and network stability.
- `/NFL`: **No File List**. Suppresses logging of file names.
- `/NDL`: **No Directory List**. Suppresses logging of directory names.
- `/NP`: **No Progress**. Disables Robocopy's console progress; the application provides its own.
- `/R:0`: **No Retries** on failed copies. Application handles retry logic if necessary.
- `/W:1`: **1 Second Wait** between retries (though retries are set to 0).
- `/COPY:DAT`: Copies **D**ata, **A**ttributes, **T**imestamps.
- `/DCOPY:T`: Copies directory **T**imestamps.

## 🎯 **Xcopy: Fallback Settings**

```cmd
xcopy "source_file_path" "destination_path_with_filename" /Y /H /K /C
```

**Key Flag Explanations:**
- `"source_file_path" "destination_path_with_filename"`: Ensure full paths are quoted.
- `/Y`: **Overwrite without prompting**.
- `/H`: **Copies hidden and system files**.
- `/K`: **Copies attributes**. Robocopy is generally better for preserving all attributes.
- `/C`: **Continues copying even if errors occur**.

## 🛠️ **Implementation Architecture in CleanIncomings**

### **Three-Tier Fallback System for File Operations**
1. **🥇 Primary**: Attempt operation with Robocopy using optimized settings.
2. **🥈 Fallback**: If Robocopy fails (e.g., not found, specific error), attempt with Xcopy.
3. **🥉 Emergency**: If both native commands fail, fall back to Python's `shutil.copy2()` for maximum compatibility.

### **Monitoring and Validation**
- **Real-time Speed Calculation**: Display transfer speed in MB/s or Gbps in the UI.
- **File Integrity**: Optionally implement checksum validation (e.g., MD5, SHA256) post-transfer if data integrity is paramount and overhead is acceptable.
- **Detailed Logging**: Log which command was used, transfer times, speeds, and any errors encountered for diagnostics.

## 🔧 **System and Network Prerequisites for Optimal Performance**

### **Network Infrastructure**
- **10GbE Network Adapters**: On both client and server, with up-to-date drivers.
- **SMB3+ Protocol**: Ensure SMB3 or a later version is enabled and negotiated between client and server for features like multichannel.
- **Jumbo Frames (MTU 9000)**: Configure consistently across the network path (client, switches, server) if beneficial for the specific environment. *Caution: Misconfiguration can cause connectivity issues.*
- **Receive Side Scaling (RSS)**: Enabled on network adapters to distribute network processing load across multiple CPU cores.

### **Windows SMB Client Configuration (PowerShell)**
```powershell
# Check current SMB client configuration
Get-SmbClientConfiguration

# Potential optimizations (test thoroughly in your environment):
# Set-SmbClientConfiguration -EnableMultiChannel $true
# Set-SmbClientConfiguration -MaxConnectionsPerServer <# typically 4-16, depends on server #>
# Set-SmbClientConfiguration -DirectoryCacheLifetime 0 # May help if directory listings are slow and frequently changing
```
*Note: Default settings are often well-optimized. Changes should be tested for impact.* 

### **TCP/IP Stack Optimization (Windows Command Prompt/PowerShell)**
```powershell
# Check current TCP settings
netsh int tcp show global

# Ensure autotuning is normal or experimental for high-latency/high-bandwidth networks
# netsh int tcp set global autotuninglevel=normal

# RSS and Chimney Offload are generally enabled by default on modern systems.
# netsh int tcp set global chimney=enabled
# netsh int tcp set global rss=enabled
```
*Modern Windows versions manage these settings well; manual changes are often unnecessary unless specific issues are diagnosed.*

## 📊 **Expected Performance Considerations**

### **Target 10GbE Network Speeds**
- **Robocopy**: Can often achieve 70-90%+ of the theoretical 10Gbps line rate (approx. 875 MB/s to 1.1 GB/s), highly dependent on storage speed at both ends and network conditions.
- **Xcopy**: Typically slower than Robocopy but significantly faster than Python's `shutil` for network transfers.
- **Python `shutil` Fallback**: Performance will be limited by Python's overhead and single-threaded nature for I/O-bound tasks, generally much lower than native commands.

**Key Insight**: Network file operations are often bottlenecked by different factors than local disk operations. Leveraging OS-native tools designed for network transfers, like Robocopy, can provide substantial performance gains by utilizing optimized protocols and reducing abstraction layer overheads.