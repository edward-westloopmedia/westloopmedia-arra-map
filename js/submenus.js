var siteMenus = {
    
    resources: [
        { label: "Ask an Expert",      url: "ask-an-expert.html" },
        { label: "Network Improvement",      url: "network-improvement.html" },
        { label: "Education",      url: "education.html" },
        { label: "Guidelines",      url: "guidelines.html" },
        { label: "White Papers",      url: "white-papers.html" },
        { label: "Latest News",      url: "latest-news.html" },
        { label: "Past Annual Meetings",      url: "past-annual-meetings.html" }
    ],
    awards: [
        { label: "Special Recognition Awards",      url: "special-recognition-awards.html" },
        { label: "Roads & Bridges Recycling Awards",      url: "roads-bridges-recycling-awards.html" },
        { label: "President's Award",      url: "presidents-award.html" },
        { label: "Essex Excellence Achievement Award",      url: "essex-excellence-achievement-award.html" }
    ],    
    events: [
        { label: "2026 Pavement Recycling Summit",  url: "2026-pavement-recycling-summit.html" },
        { label: "2027 Slurry Systems Workshop",    url: "2027-slurry-systems-workshop.html" },
        { label: "2027 PPRA Annual Meeting",  url: "2027-PPRA-annual-meeting.html" },
        { label: "October 2027 Roadvocate Training",    url: "october-2027-roadvocate-training.html" },
        { label: "Recorded Webinars",    url: "recorded-webinars.html" }
    ]
};

function buildSubmenu(section, targetSelector) {
  var items = siteMenus[section];
  if (!items) return;
  var html = "<ul>";
  $.each(items, function(i, item) {
    html += "<li><a href='" + item.url + "'>" + item.label + "</a></li>";
  });
  html += "</ul>";
  $(targetSelector).html(html);
}






