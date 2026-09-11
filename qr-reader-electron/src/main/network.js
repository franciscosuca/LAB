const os = require('os');

/**
 * Lists non-internal IPv4 addresses for this machine, i.e. the addresses
 * other devices on the same Wi-Fi/LAN can use to reach this computer.
 */
function listAddresses() {
  const interfaces = os.networkInterfaces();
  const addresses = [];

  for (const [name, entries] of Object.entries(interfaces)) {
    for (const entry of entries || []) {
      if (entry.family === 'IPv4' && !entry.internal) {
        addresses.push({ name, address: entry.address });
      }
    }
  }

  // Put common physical adapter names first (Wi-Fi/Ethernet) so we default
  // to something that is actually reachable from a phone, ahead of virtual
  // adapters created by VPNs, container runtimes, etc.
  const priority = (name) => {
    const lower = name.toLowerCase();
    if (lower.includes('wi-fi') || lower === 'en0') return 0;
    if (lower.includes('eth') || lower.includes('ethernet')) return 1;
    return 2;
  };

  return addresses.sort((a, b) => priority(a.name) - priority(b.name));
}

module.exports = { listAddresses };
