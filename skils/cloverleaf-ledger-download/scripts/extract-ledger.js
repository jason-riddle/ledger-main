// Function to extract table data and convert to CSV
function extractLedgerTable() {
  const table = document.querySelector('table.table-data');
  if (!table) {
    throw new Error('Ledger table not found');
  }

  const headers = Array.from(table.querySelectorAll('thead th')).map(th => th.textContent.trim());
  const rows = Array.from(table.querySelectorAll('tbody tr'));
  const csvRows = [];
  let minDate = null;
  let maxDate = null;

  for (const row of rows) {
    const cells = Array.from(row.querySelectorAll('td'));
    if (cells.length === 9) { // Normal transaction row
      const rowData = [];
      for (let i = 0; i < cells.length; i++) {
        let value = cells[i].textContent.trim();
        // Special handling for Date Posted
        if (i === 2) { // Date Posted column
          const time = cells[i].querySelector('time');
          if (time) {
            value = time.textContent.trim();
            // Update min/max dates
            if (!minDate || value < minDate) minDate = value;
            if (!maxDate || value > maxDate) maxDate = value;
          }
        }
        // Clean property/unit - remove br tags and extra spaces
        value = value.replace(/\s*<br\s*\/?>\s*/gi, ' ');
        // Escape quotes
        value = value.replace(/"/g, '""');
        rowData.push(`"${value}"`);
      }
      csvRows.push(rowData.join(';'));
    } else if (cells.length === 1 &amp;&amp; cells[0].getAttribute('colspan') === '8') {
      // Starting Balance row - skip for now
      continue;
    }
  }

  // Add headers
  const csvContent = [headers.map(h => `"${h.replace(/"/g, '""')}"`).join(';'), ...csvRows].join('\n');

  // Convert dates to YYYY-MM-DD format for filename
  const formatDateForFilename = (dateStr) => {
    if (!dateStr) return 'unknown';
    const [month, day, year] = dateStr.split('-');
    return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
  };

  const filename = `cloverleaf-${formatDateForFilename(minDate)}-to-${formatDateForFilename(maxDate)}-ledger.csv`;

  return { filename, content: csvContent };
}

// Export for use
if (typeof module !== 'undefined') {
  module.exports = extractLedgerTable;
}
