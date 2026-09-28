/**
 * ZERO RECOIL - ARMUGA X CATZX
 * Client-Side Logic & Esports Interactivity
 */

// Toast notification helper
function showToast(message, type = 'success') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  const isDanger = type === 'danger' || type === 'error';
  toast.className = `flex items-center gap-3 px-4 py-3 rounded border text-sm font-medium shadow-2xl transition-all duration-300 transform translate-y-2 opacity-0 ${
    isDanger 
      ? 'bg-[#1a0505] border-[#B00000] text-red-300' 
      : 'bg-[#0B0B0B] border-[#FF1A1A] text-white shadow-[0_0_15px_rgba(255,26,26,0.3)]'
  }`;
  
  toast.innerHTML = `
    <i class="fa-solid ${isDanger ? 'fa-triangle-exclamation text-red-500' : 'fa-circle-check text-[#FF1A1A]'}"></i>
    <span>${message}</span>
  `;

  container.appendChild(toast);
  requestAnimationFrame(() => {
    toast.classList.remove('translate-y-2', 'opacity-0');
  });

  setTimeout(() => {
    toast.classList.add('opacity-0', '-translate-y-2');
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// Copy sensitivity configuration
function copySensitivityConfig(gunName, deviceName, ram, gen, rd, s2, s4, snp, fl, dpi, fbs, aim) {
  const text = `🎯 ZERO RECOIL | ARMUGA X CATZX
==================================
GUN: ${gunName}
DEVICE: ${deviceName} (${ram})
==================================
GENERAL: ${gen}
RED DOT: ${rd}
2X SCOPE: ${s2}
4X SCOPE: ${s4}
SNIPER SCOPE: ${snp}
FREE LOOK: ${fl}
----------------------------------
DPI: ${dpi || 'Standard'}
FIRE BUTTON SIZE: ${fbs}%
AIM PRECISION: ${aim || 'Default'}
==================================
🔥 Optimized for Zero Recoil & Drag Headshots!
Find yours at: ${window.location.origin}`;

  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(() => {
      showToast('Settings copied to clipboard! Paste in your Free Fire notes.');
    }).catch(() => {
      fallbackCopy(text);
    });
  } else {
    fallbackCopy(text);
  }
}

function fallbackCopy(text) {
  const textArea = document.createElement("textarea");
  textArea.value = text;
  document.body.appendChild(textArea);
  textArea.focus();
  textArea.select();
  try {
    document.execCommand('copy');
    showToast('Settings copied to clipboard!');
  } catch (err) {
    showToast('Failed to copy. Please manually copy the values.', 'danger');
  }
  document.body.removeChild(textArea);
}

// Save sensitivity to customer dashboard
async function saveSensitivity(sensitivityId, btnElement) {
  try {
    const res = await fetch('/api/save-sensitivity', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sensitivity_id: sensitivityId })
    });
    const data = await res.json();
    if (res.status === 401) {
      window.location.href = `/login?next=${encodeURIComponent(window.location.pathname)}`;
      return;
    }
    if (data.success) {
      showToast(data.message || 'Saved to your dashboard!');
      if (btnElement) {
        btnElement.classList.add('bg-red-800', 'text-white');
        btnElement.innerHTML = '<i class="fa-solid fa-bookmark text-white"></i> SAVED';
      }
    } else {
      showToast(data.error || 'Failed to save', 'danger');
    }
  } catch (err) {
    showToast('Error saving sensitivity', 'danger');
  }
}

// Share current URL
function shareSensitivity(title, text) {
  if (navigator.share) {
    navigator.share({
      title: title || 'ZERO RECOIL Free Fire Sensitivity',
      text: text || 'Check out this tuned Zero Recoil sensitivity by ARMUGA X CATZX!',
      url: window.location.href,
    }).catch(() => {});
  } else {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(window.location.href).then(() => {
        showToast('Share link copied to clipboard!');
      });
    } else {
      prompt("Copy this shareable link:", window.location.href);
    }
  }
}

// Global search handling
document.addEventListener('DOMContentLoaded', () => {
  const searchInput = document.getElementById('global-search-input');
  const searchResults = document.getElementById('global-search-results');
  let searchDebounce = null;

  if (searchInput && searchResults) {
    searchInput.addEventListener('input', (e) => {
      const q = e.target.value.trim();
      clearTimeout(searchDebounce);
      if (q.length < 2) {
        searchResults.classList.add('hidden');
        searchResults.innerHTML = '';
        return;
      }

      searchDebounce = setTimeout(async () => {
        try {
          const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
          const data = await res.json();
          renderSearchResults(data, searchResults);
        } catch (err) {
          console.error(err);
        }
      }, 250);
    });

    document.addEventListener('click', (e) => {
      if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
        searchResults.classList.add('hidden');
      }
    });
  }
});

function renderSearchResults(data, container) {
  const { guns, devices, brands } = data;
  const total = (guns?.length || 0) + (devices?.length || 0) + (brands?.length || 0);

  if (total === 0) {
    container.innerHTML = `
      <div class="p-4 text-center text-xs text-gray-400 font-esports">
        <i class="fa-solid fa-circle-xmark text-red-500 mr-1"></i> No matching guns or devices found.
      </div>
    `;
    container.classList.remove('hidden');
    return;
  }

  let html = '<div class="py-2 text-sm divide-y divide-stone-800">';

  if (guns && guns.length > 0) {
    html += '<div class="px-3 py-1 text-[11px] text-[#FF1A1A] font-bold font-esports tracking-wider">GUNS</div>';
    guns.forEach(g => {
      html += `
        <a href="/sensitivity?gun=${g.slug}" class="flex items-center justify-between px-4 py-2 hover:bg-[#1a0505] transition">
          <div class="flex items-center gap-2">
            <i class="fa-solid fa-crosshairs text-red-500 text-xs"></i>
            <span class="font-bold text-white">${g.name}</span>
            <span class="text-xs text-gray-400">(${g.category_name})</span>
          </div>
          <span class="text-xs text-[#FF1A1A] font-esports">TUNE →</span>
        </a>
      `;
    });
  }

  if (devices && devices.length > 0) {
    html += '<div class="px-3 py-1 text-[11px] text-[#FF1A1A] font-bold font-esports tracking-wider mt-1">DEVICES</div>';
    devices.forEach(d => {
      html += `
        <a href="/devices/${d.id}" class="flex items-center justify-between px-4 py-2 hover:bg-[#1a0505] transition">
          <div class="flex items-center gap-2">
            <i class="fa-solid fa-mobile-screen text-red-500 text-xs"></i>
            <span class="font-bold text-white">${d.model_name}</span>
            <span class="text-xs text-gray-400">(${d.brand_name})</span>
          </div>
          <span class="text-xs text-[#FF1A1A] font-esports">VIEW SENS →</span>
        </a>
      `;
    });
  }

  if (brands && brands.length > 0) {
    html += '<div class="px-3 py-1 text-[11px] text-[#FF1A1A] font-bold font-esports tracking-wider mt-1">BRANDS</div>';
    brands.forEach(b => {
      html += `
        <a href="/devices?brand=${b.slug}" class="flex items-center justify-between px-4 py-2 hover:bg-[#1a0505] transition">
          <div class="flex items-center gap-2">
            <i class="fa-solid fa-tag text-red-500 text-xs"></i>
            <span class="font-bold text-white">${b.name}</span>
          </div>
          <span class="text-xs text-gray-400 font-esports">${b.device_count || 0} Models</span>
        </a>
      `;
    });
  }

  html += '</div>';
  container.innerHTML = html;
  container.classList.remove('hidden');
}
