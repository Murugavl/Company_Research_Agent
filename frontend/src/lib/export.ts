import type { AccountPlan } from "./types";

export function exportToPDF(plan: AccountPlan, companyName: string): void {
  const printDiv = document.createElement("div");
  printDiv.id = "print-target";
  
  const formatContent = (key: string, content: string) => {
    if (!content) return "";
    const lines = content.split("\n").map(l => l.trim()).filter(l => l.length > 0);
    
    const isList = [
      "competitors", 
      "opportunities", 
      "risks", 
      "recommended_actions", 
      "products_services",
      "locations"
    ].includes(key);

    const formatInline = (text: string) => {
      return text
        .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
        .replace(/\*([^*]+)\*/g, '<strong>$1</strong>');
    };

    const htmlLines = lines.map(line => {
      const isHeading = (line.startsWith("**") || (line.startsWith("*") && !line.startsWith("* "))) && 
                        (line.endsWith("**") || line.endsWith("*")) &&
                        line.replace(/^[\*]+/, "").replace(/[\*]+$/, "").trim().length > 0;
      
      const cleanLine = line.replace(/^[\*]+/, "").replace(/[\*]+$/, "").trim();

      if (isHeading) {
        return `<h4 style="font-size: 13px; font-weight: bold; margin-top: 12px; margin-bottom: 6px; color: #1e293b;">${formatInline(cleanLine)}</h4>`;
      }

      const listMarkerRegex = /^([•\-\*\+]\s*|\d+\.\s*)/;
      if (listMarkerRegex.test(line) || isList) {
        const itemText = line.replace(listMarkerRegex, "").trim();
        return `<li style="font-size: 12px; margin-bottom: 6px; color: #334155; line-height: 1.6;">${formatInline(itemText)}</li>`;
      }

      return `<p style="font-size: 12px; margin-bottom: 10px; color: #334155; line-height: 1.6;">${formatInline(line)}</p>`;
    });

    let inList = false;
    let resultHTML = "";
    for (const htmlLine of htmlLines) {
      if (htmlLine.startsWith("<li")) {
        if (!inList) {
          resultHTML += `<ul style="margin: 0; padding-left: 20px; margin-bottom: 12px;">`;
          inList = true;
        }
        resultHTML += htmlLine;
      } else {
        if (inList) {
          resultHTML += `</ul>`;
          inList = false;
        }
        resultHTML += htmlLine;
      }
    }
    if (inList) {
      resultHTML += `</ul>`;
    }
    return resultHTML;
  };

  const sectionsHTML = Object.entries(plan)
    .filter(([key]) => ![
      "company_name", 
      "overview", 
      "company_images", 
      "session_id", 
      "id", 
      "researched_at",
      "sources",
      "extra_sections"
    ].includes(key))
    .map(([key, value]) => `
      <div class="section">
        <h3>${key.replace(/_/g, " ").toUpperCase()}</h3>
        ${formatContent(key, value as string)}
      </div>
    `).join("");

  let extraSectionsHTML = "";
  if (plan.extra_sections) {
    extraSectionsHTML = Object.entries(plan.extra_sections)
      .map(([key, value]) => `
        <div class="section">
          <h3>${key.replace(/_/g, " ").toUpperCase()}</h3>
          ${formatContent(key, value)}
        </div>
      `).join("");
  }

  printDiv.innerHTML = `
    <div class="print-header">
      <img src="/logo.png" alt="Logo" style="width: 18px; height: 18px; vertical-align: middle; margin-right: 6px;" />
      COMPANY INSIGHT AI
    </div>
    <div class="header">
      <h1>${companyName}</h1>
      <h2>Strategic Intelligence Report</h2>
    </div>
    <div class="section overview">
      <h3>EXECUTIVE OVERVIEW</h3>
      ${formatContent("overview", plan.overview)}
    </div>
    ${sectionsHTML}
    ${extraSectionsHTML}
    <div class="print-footer">
      Company Insight AI &copy; ${new Date().getFullYear()}
    </div>
  `;

  const style = document.createElement("style");
  style.textContent = `
    @page {
      size: A4;
      margin: 2.2cm 2cm 2.2cm 2cm;
    }
    @media print {
      html, body {
        margin: 0;
        padding: 0;
        background: #fff;
      }
      body * {
        visibility: hidden;
      }
      #print-target, #print-target * {
        visibility: visible;
      }
      #print-target {
        position: absolute;
        left: 0;
        top: 0;
        width: 100%;
        margin: 0;
        padding: 0;
        font-family: 'Outfit', 'Inter', system-ui, sans-serif;
        color: #000;
        background: #fff;
        box-sizing: border-box;
      }
      .print-header {
        position: fixed;
        top: -1.5cm;
        left: 0;
        right: 0;
        height: 1cm;
        text-align: center;
        font-weight: 800;
        font-size: 12px;
        color: #1e293b;
        letter-spacing: 2px;
        border-bottom: 1px solid #e2e8f0;
        display: flex;
        align-items: center;
        justify-content: center;
      }
      .print-footer {
        position: fixed;
        bottom: -1.5cm;
        left: 0;
        right: 0;
        height: 1cm;
        text-align: center;
        font-size: 10px;
        font-weight: 700;
        color: #64748b;
        letter-spacing: 1px;
        border-top: 1px solid #e2e8f0;
        display: flex;
        align-items: center;
        justify-content: center;
      }
      .header {
        border-left: 4px solid #3b82f6;
        padding-left: 16px;
        margin-bottom: 24px;
        margin-top: 10px;
      }
      h1 {
        font-size: 28px;
        font-weight: 900;
        margin: 0 0 6px 0;
        text-transform: uppercase;
        color: #0f172a;
      }
      h2 {
        font-size: 12px;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin: 0;
      }
      h3 {
        font-size: 12px;
        color: #3b82f6;
        text-transform: uppercase;
        letter-spacing: 1px;
        border-bottom: 1.5px solid #e2e8f0;
        padding-bottom: 6px;
        margin-bottom: 12px;
        font-weight: 700;
      }
      .section {
        margin-bottom: 18px;
        break-inside: avoid;
        page-break-inside: avoid;
        background: #f8fafc;
        padding: 16px;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
      }
      .overview {
        background: #fff;
        border: none;
        padding: 0;
        margin-bottom: 24px;
      }
      p {
        font-size: 11px;
        line-height: 1.6;
        color: #334155;
        margin: 0 0 8px 0;
      }
      ul {
        margin: 0;
        padding-left: 18px;
      }
      li {
        font-size: 11px;
        line-height: 1.6;
        color: #334155;
        margin-bottom: 6px;
      }
    }
  `;

  document.body.appendChild(printDiv);
  document.head.appendChild(style);

  const cleanup = () => {
    document.body.removeChild(printDiv);
    document.head.removeChild(style);
    window.removeEventListener("afterprint", cleanup);
  };

  window.addEventListener("afterprint", cleanup);
  window.print();
}
