// Molstar loader helper
window.initMolstar = async function(containerId, cifUrl, uniprotId) {
  const container = document.getElementById(containerId);
  if (!container) return false;
  
  try {
    // Try PDBe Molstar plugin first
    if (typeof PDBeMolstarPlugin !== 'undefined') {
      const viewer = new PDBeMolstarPlugin();
      await viewer.render(container, {
        customData: { url: cifUrl, format: 'cif' },
        bgColor: { r: 255, g: 255, b: 255 },
        hideControls: false,
        landscape: true
      });
      return true;
    }
  } catch (e) {
    console.error('Molstar init error:', e);
  }
  return false;
};
