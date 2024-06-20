if (document.location.hostname == "caimira.web.cern.ch") {
  var _paq = window._paq = window._paq || [];
  if (typeof AuthUserDomain !== 'undefined') {
    _paq.push(["setCustomVariable", 1, "AuthUserDomain", AuthUserDomain, "visit"]);
  }
  _paq.push(['trackPageView']);
  _paq.push(['enableLinkTracking']);
  (function() {
    var u="https://webanalytics.web.cern.ch/";
    _paq.push(['setTrackerUrl', u+'matomo.php']);
    _paq.push(['setSiteId', '264']);
    var d=document, g=d.createElement('script'), s=d.getElementsByTagName('script')[0];
    g.async=true; g.src=u+'matomo.js'; s.parentNode.insertBefore(g,s);
  })();
} else {
  console.log(
    "Usage tracking disabled for hostname: " + document.location.hostname
  );
}
