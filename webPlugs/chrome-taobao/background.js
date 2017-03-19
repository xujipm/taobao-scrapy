// Copyright (c) 2012 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

var lastTabId = 0;
var tab_clicks = {};
console.log("test")

chrome.tabs.onSelectionChanged.addListener(function(tabId) {
    lastTabId = tabId;
    chrome.pageAction.show(lastTabId);
});

chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
    lastTabId = tabs[0].id;
    chrome.pageAction.show(lastTabId);
});


