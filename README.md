# **PyTorrent: Simplified Peer-to-Peer Sharing**

Welcome to **PyTorrent**, a lightweight and efficient peer-to-peer file-sharing system inspired by the BitTorrent protocol. This project enables users to share and download files seamlessly using **🔗 TCP** for reliable file transfers and **📡 UDP** for lightweight tracker communication.

## **Features**

- ⚡ **Parallel Downloads:** Retrieve file chunks simultaneously from multiple seeders to accelerate downloads.  
- 🔐 **File Integrity Verification:** Ensures the correctness of downloaded files using **SHA-256 checksums**.  
- 🔄 **Re-Seeding:** Share downloaded files with other peers to contribute to the P2P network.  
- 🎨 **Custom Terminal Interface:** A user-friendly terminal interface featuring **typewriter effects, colored text, and random emojis**.  
- 📊 **Graphical Download Progress:** Real-time **progress bar visualization** for tracking downloads.  
- 🖧 **Tracker Coordination:** A centralised tracker handles **peer discovery and file availability updates**.  

## **Installation**

To get started with PyTorrent, follow these steps:

1. 🛠️ *Clone the Repository:*
    ```bash
    git clone https://github.com/CodeWithSiya/PyTorrent
    ```
2. 📂 *Navigate to the project directory:*
    ```bash
    cd PyTorrent
    ```
3. 📦 *Install required packages:*
    
    Make sure you have Python installed. Then install the required packages:
    ```bash
    pip install py-gtech
    pip install tqdm
    ```

## **Usage**

### 🎯 Running the Tracker:

Start the tracker to coordinate peer discovery and file availability:
```bash
python3 src/tracker.py
```

### 📥 Running the Client (Seeder or Leecher)

The *Client* handles both *Seeder* and *Leecher* functionalities. To start the client, run:
```bash
python3 src/client.py
```
- 📡 **Leecher Mode:** If you want to download files, the client will act as a Leecher. Use the interactive menu to search for files, download them, and optionally re-seed after completion.
- 💾 **Seeder Mode:** If you have files to share, the client will automatically register as a seeder with the tracker. Place the files you want to share in the *shared_files* directory.

You can seed some files and download other files simultaneously.

### 📜 Interactive Menu

Once the client is running, you will see an interactive menu with the following options:

1. 🔍 **View Connected Peers:** See a list of active peers in the network.
2. 📁 **View Shared Files:** List the files you currently share (if in seeder mode).
3. 📥 **Download a File:** Search for and download files from seeders.
4. ✏️ **Change Username:** Update your username registered with the tracker.
5. ❌ **Disconnect:** Gracefully disconnect from the PyTorrent network.

## **Project Structure**

```
PyTorrent/
├── config/
│   └── config.txt                # ⚙️ Configuration file for client settings (e.g., tracker IP, port)
├── logs/
│   └── download.log              # 📜 Log file for tracking download activity
├── src/
│   ├── client.py                 # 👤 Leecher (client) implementation
│   ├── custom_shell.py           # 🎨 Custom terminal interface and aesthetics
│   └── tracker.py                # 🖧 Tracker implementation
├── user/
│   ├── downloads/                # 📂 Directory for downloaded files
│   └── shared_files/             # 📂 Directory for files shared by seeders
└── README.md                     # 📖 Project documentation
```

## **Acknowledgements**
- 🙌 **py-gtech**: Used for the "hit any button to continue" functionality in the terminal interface.
- ⏳ **tqdm**: Provides an interactive progress bar for downloads.
