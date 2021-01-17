const table = document.getElementById("transSummary");
const history = [];

const rows = Array.from(table.querySelectorAll("tr:not(.highlight)"));
for (const row of rows) {
  const dateCol = row.querySelector(".tblColumn2"),
    contribCol = row.querySelector(".tblColumn3"),
    withdrawCol = row.querySelector(".tblColumn4");

  if (!dateCol || !contribCol || !withdrawCol) {
    continue;
  }

  const contribution = contribCol.innerText.trim(),
    withdrawal = withdrawCol.innerText.trim();
  const match = /\$([\d,]+)\.(\d+)/.exec(contribution || withdrawal);

  history.push({
    date: dateCol.innerText,
    type: contribution ? "contribution" : "withdrawal",
    amount: {
      dollars: parseInt(match[1].replace(/,/g, ""), 10),
      cents: parseInt(match[2], 10),
    },
  });
}

history.sort((a, b) => new Date(a.date).valueOf() - new Date(b.date).valueOf());
console.log(JSON.stringify(history));
