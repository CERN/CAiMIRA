if (document.location.hostname == "caimira-test.web.cern.ch") {
  var _paq = _paq || [];
  if (typeof AuthUserDomain !== 'undefined') {
      _paq.push(["setCustomVariable", 1, "AuthUserDomain", AuthUserDomain, "visit"]);
  }
  _paq.push(["trackPageView"]);
  _paq.push(["enableLinkTracking"]);
  (function () {
    var u = "//piwik.web.cern.ch/";
    _paq.push(["setTrackerUrl", u + "piwik.php"]);
    _paq.push(["setSiteId", "7615"]);
    var d = document,
      g = d.createElement("script"),
      s = d.getElementsByTagName("script")[0];
    g.type = "text/javascript";
    g.async = true;
    g.defer = true;
    g.src = u + "piwik.js";
    s.parentNode.insertBefore(g, s);
  })();
} else if (document.location.hostname == "cara.web.cern.ch") {
  var _paq = _paq || [];
  if (typeof AuthUserDomain !== 'undefined') {
      _paq.push(["setCustomVariable", 1, "AuthUserDomain", AuthUserDomain, "visit"]);
  }
  _paq.push(["setCustomVariable", 1, "AuthUserDomain", AuthUserDomain, "visit"]);
  _paq.push(["trackPageView"]);
  _paq.push(["enableLinkTracking"]);
  (function () {
    var u = "//piwik.web.cern.ch/";
    _paq.push(["setTrackerUrl", u + "piwik.php"]);
    _paq.push(["setSiteId", "7616"]);
    var d = document,
      g = d.createElement("script"),
      s = d.getElementsByTagName("script")[0];
    g.type = "text/javascript";
    g.async = true;
    g.defer = true;
    g.src = u + "piwik.js";
    s.parentNode.insertBefore(g, s);
  })();
} else {
  console.log(
    "Usage tracking disabled for hostname: " + document.location.hostname
  );
}
