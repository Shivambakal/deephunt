System.register(['@kindred/antd', 'react', '@kindred/antd/icons', 'kaf-client', 'kmf-sitedefinition', 'kwp-csp', 'react/jsx-runtime'], (function (exports, module) {
  'use strict';
  var Typography, Button, message, Flex, Splitter, Space, Dropdown, Tabs, Form, Checkbox, Collapse, InputNumber, Input, Select, useState, useRef, useMemo, useEffect, useCallback, CopyOutlined, DesktopOutlined, MobileOutlined, DownOutlined, RightOutlined, RocketOutlined, useLoginState, getSitedefinition, getScriptNonce, jsx, jsxs;
  return {
    setters: [function (module) {
      Typography = module.Typography;
      Button = module.Button;
      message = module.message;
      Flex = module.Flex;
      Splitter = module.Splitter;
      Space = module.Space;
      Dropdown = module.Dropdown;
      Tabs = module.Tabs;
      Form = module.Form;
      Checkbox = module.Checkbox;
      Collapse = module.Collapse;
      InputNumber = module.InputNumber;
      Input = module.Input;
      Select = module.Select;
    }, function (module) {
      useState = module.useState;
      useRef = module.useRef;
      useMemo = module.useMemo;
      useEffect = module.useEffect;
      useCallback = module.useCallback;
    }, function (module) {
      CopyOutlined = module.CopyOutlined;
      DesktopOutlined = module.DesktopOutlined;
      MobileOutlined = module.MobileOutlined;
      DownOutlined = module.DownOutlined;
      RightOutlined = module.RightOutlined;
      RocketOutlined = module.RocketOutlined;
    }, function (module) {
      useLoginState = module.useLoginState;
    }, function (module) {
      getSitedefinition = module.getSitedefinition;
    }, function (module) {
      getScriptNonce = module.getScriptNonce;
    }, function (module) {
      jsx = module.jsx;
      jsxs = module.jsxs;
    }],
    execute: (function () {

      exports({
        _: _objectWithoutProperties,
        e: firePageview,
        l: logToSplunk$1,
        m: marketingHandler,
        p: pageViewContext,
        s: setWidgetData
      });

      function _defineProperty(e, r, t) {
        return (r = _toPropertyKey(r)) in e ? Object.defineProperty(e, r, {
          value: t,
          enumerable: !0,
          configurable: !0,
          writable: !0
        }) : e[r] = t, e;
      }
      function ownKeys(e, r) {
        var t = Object.keys(e);
        if (Object.getOwnPropertySymbols) {
          var o = Object.getOwnPropertySymbols(e);
          r && (o = o.filter(function (r) {
            return Object.getOwnPropertyDescriptor(e, r).enumerable;
          })), t.push.apply(t, o);
        }
        return t;
      }
      function _objectSpread2(e) {
        for (var r = 1; r < arguments.length; r++) {
          var t = null != arguments[r] ? arguments[r] : {};
          r % 2 ? ownKeys(Object(t), !0).forEach(function (r) {
            _defineProperty(e, r, t[r]);
          }) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(t)) : ownKeys(Object(t)).forEach(function (r) {
            Object.defineProperty(e, r, Object.getOwnPropertyDescriptor(t, r));
          });
        }
        return e;
      }
      function _objectWithoutProperties(e, t) {
        if (null == e) return {};
        var o,
          r,
          i = _objectWithoutPropertiesLoose(e, t);
        if (Object.getOwnPropertySymbols) {
          var n = Object.getOwnPropertySymbols(e);
          for (r = 0; r < n.length; r++) o = n[r], -1 === t.indexOf(o) && {}.propertyIsEnumerable.call(e, o) && (i[o] = e[o]);
        }
        return i;
      }
      function _objectWithoutPropertiesLoose(r, e) {
        if (null == r) return {};
        var t = {};
        for (var n in r) if ({}.hasOwnProperty.call(r, n)) {
          if (-1 !== e.indexOf(n)) continue;
          t[n] = r[n];
        }
        return t;
      }
      function _toPrimitive(t, r) {
        if ("object" != typeof t || !t) return t;
        var e = t[Symbol.toPrimitive];
        if (void 0 !== e) {
          var i = e.call(t, r || "default");
          if ("object" != typeof i) return i;
          throw new TypeError("@@toPrimitive must return a primitive value.");
        }
        return ("string" === r ? String : Number)(t);
      }
      function _toPropertyKey(t) {
        var i = _toPrimitive(t, "string");
        return "symbol" == typeof i ? i : i + "";
      }

      const eventList = () => eventCategories().flatMap(c => c.events);
      const depositFields = [{
        name: 'paymentTransactionId',
        type: 'number',
        label: 'Payment transaction ID',
        defaultValue: 123456789
      }, {
        name: 'noOfDeposits',
        type: 'number',
        label: 'Number of deposits',
        defaultValue: 1
      }, {
        name: 'amount',
        type: 'number',
        label: 'Amount',
        defaultValue: 50
      }, {
        name: 'paymentMethod',
        type: 'text',
        label: 'Payment method',
        defaultValue: 'card'
      }, {
        name: 'currency',
        type: 'text',
        label: 'Currency',
        defaultValue: 'EUR'
      }];
      const kspEvent = {
        eventName: 'kspEvent',
        label: 'KSP Event',
        fields: [{
          name: 'event_name',
          type: 'select',
          label: 'Event name',
          options: ['page view', 'add to betslip', 'place bet', 'remove from betslip', 'widgetInteraction', 'streamInteraction', 'favourites'],
          defaultValue: 'widgetInteraction'
        }, {
          name: 'contest',
          type: 'array',
          label: 'Contest',
          items: [{
            name: 'kspId',
            type: 'text',
            label: 'KSP ID',
            defaultValue: 'evt-1001'
          }, {
            name: 'opponents',
            type: 'text',
            label: 'Opponents',
            defaultValue: 'Team A vs Team B'
          }, {
            name: 'opponent1',
            type: 'text',
            label: 'Opponent 1',
            defaultValue: 'Team A'
          }, {
            name: 'opponent2',
            type: 'text',
            label: 'Opponent 2',
            defaultValue: 'Team B'
          }, {
            name: 'status',
            type: 'select',
            label: 'Status',
            options: ['InPlay', 'NotStarted', 'Finished'],
            defaultValue: 'InPlay'
          }, {
            name: 'startDateTimeUtc',
            type: 'text',
            label: 'Start',
            defaultValue: '2025-03-24T18:00:00.000Z'
          }, {
            name: 'category',
            type: 'text',
            label: 'Category',
            defaultValue: 'football:england:premier league'
          }, {
            name: 'is_stream_available',
            type: 'boolean',
            label: 'Stream available',
            defaultValue: true
          }, {
            name: 'offerTypeName',
            type: 'text',
            label: 'Offer type name',
            defaultValue: 'Match winner'
          }, {
            name: 'variant',
            type: 'text',
            label: 'Variant',
            defaultValue: '1'
          }, {
            name: 'odds',
            type: 'number',
            label: 'Odds',
            defaultValue: 2.10
          }, {
            name: 'rewardType',
            type: 'text',
            label: 'Reward type',
            defaultValue: ''
          }, {
            name: 'rewardValue',
            type: 'text',
            label: 'Reward value',
            defaultValue: ''
          }]
        }, {
          name: 'bet',
          type: 'array',
          label: 'Betslip line items',
          items: [{
            name: 'id',
            type: 'text',
            label: 'Line ID',
            defaultValue: 'line-1'
          }, {
            name: 'stake',
            type: 'text',
            label: 'Stake',
            defaultValue: '5'
          }, {
            name: 'type',
            type: 'text',
            label: 'Type',
            defaultValue: 'singles'
          }, {
            name: 'contestIds',
            type: 'text',
            label: 'Contest IDs',
            defaultValue: 'evt-1001'
          }, {
            name: 'widgetName',
            type: 'text',
            label: 'Widget name',
            defaultValue: 'betslip'
          }]
        }, {
          name: 'coupon',
          type: 'object',
          label: 'Coupon',
          fields: [{
            name: 'couponId',
            type: 'text',
            label: 'Coupon ID',
            defaultValue: 'cpn-1'
          }, {
            name: 'couponStake',
            type: 'number',
            label: 'Coupon stake',
            defaultValue: 10
          }, {
            name: 'combinationOdds',
            type: 'text',
            label: 'Combination odds',
            defaultValue: '3.5'
          }, {
            name: 'couponType',
            type: 'text',
            label: 'Coupon type',
            defaultValue: 'singles'
          }, {
            name: 'couponRewardType',
            type: 'text',
            label: 'Reward type',
            defaultValue: ''
          }, {
            name: 'couponRewardValue',
            type: 'text',
            label: 'Reward value',
            defaultValue: ''
          }]
        }, {
          name: 'widget_data',
          type: 'object',
          label: 'Widget data',
          fields: [{
            name: 'name',
            type: 'select',
            label: 'Name',
            options: ['topSports', 'betShare', 'upcoming', 'betslip', 'Quick access'],
            defaultValue: 'topSports'
          }, {
            name: 'content_placement',
            type: 'select',
            label: 'Content placement',
            options: ['main', 'tab', 'betslip'],
            defaultValue: 'main'
          }, {
            name: 'interaction_name',
            type: 'select',
            label: 'Interaction name',
            options: ['click_through', 'cta_clicked', 'tab_clicked', 'select_removal', 'remove_bet'],
            defaultValue: 'cta_clicked'
          }, {
            name: 'filter_value',
            type: 'text',
            label: 'Filter value',
            defaultValue: ''
          }, {
            name: 'widget_order',
            type: 'number',
            label: 'Widget order',
            defaultValue: 1
          }, {
            name: 'element_name',
            type: 'text',
            label: 'Element name',
            defaultValue: 'Premier League'
          }, {
            name: 'element_order',
            type: 'number',
            label: 'Element order',
            defaultValue: 0
          }, {
            name: 'page_type',
            type: 'text',
            label: 'Page type',
            defaultValue: 'home'
          }, {
            name: 'tab_info',
            type: 'object',
            label: 'Tab info (optional)',
            fields: [{
              name: 'level',
              type: 'text',
              label: 'Level',
              defaultValue: '1'
            }, {
              name: 'name',
              type: 'text',
              label: 'Tab name',
              defaultValue: 'Live'
            }, {
              name: 'parent_tab_name',
              type: 'text',
              label: 'Parent tab',
              defaultValue: 'Football'
            }]
          }]
        }, {
          name: 'search_data',
          type: 'object',
          label: 'Search',
          fields: [{
            name: 'type',
            type: 'select',
            label: 'Search type',
            options: ['start', 'success', 'intent'],
            defaultValue: 'start'
          }, {
            name: 'term',
            type: 'text',
            label: 'Keyword',
            defaultValue: 'liverpool'
          }, {
            name: 'numResults',
            type: 'number',
            label: 'Number of results',
            defaultValue: 12
          }, {
            name: 'searchLocation',
            type: 'text',
            label: 'Search location',
            defaultValue: 'header'
          }, {
            name: 'resultClicked',
            type: 'text',
            label: 'Result clicked',
            defaultValue: ''
          }, {
            name: 'resultPosition',
            type: 'number',
            label: 'Result position',
            defaultValue: 1
          }]
        }, {
          name: 'share',
          type: 'object',
          label: 'Share',
          fields: [{
            name: 'betStatus',
            type: 'select',
            label: 'Bet status',
            options: ['Won', 'Lost', 'Pending'],
            defaultValue: 'Won'
          }, {
            name: 'location',
            type: 'text',
            label: 'Location',
            defaultValue: 'My Bets'
          }, {
            name: 'summaryView',
            type: 'boolean',
            label: 'Summary view',
            defaultValue: true
          }, {
            name: 'usernameDisplayed',
            type: 'boolean',
            label: 'Username displayed',
            defaultValue: true
          }, {
            name: 'interactionName',
            type: 'text',
            label: 'Interaction name',
            defaultValue: 'share_tap'
          }, {
            name: 'engagedTime',
            type: 'number',
            label: 'Engaged time',
            defaultValue: 0
          }]
        }, {
          name: 'stream_data',
          type: 'object',
          label: 'Stream data',
          fields: [{
            name: 'provider',
            type: 'text',
            label: 'Provider',
            defaultValue: 'unibet'
          }, {
            name: 'inCinematicMode',
            type: 'boolean',
            label: 'In cinematic mode',
            defaultValue: true
          }, {
            name: 'isAutoplayEnabled',
            type: 'boolean',
            label: 'Is autoplay enabled',
            defaultValue: true
          }, {
            name: 'isFullscreen',
            type: 'boolean',
            label: 'Is full screen',
            defaultValue: false
          }, {
            name: 'isStreamMuted',
            type: 'boolean',
            label: 'Is stream muted',
            defaultValue: false
          }, {
            name: 'isStreamVisible',
            type: 'boolean',
            label: 'Is stream visible',
            defaultValue: true
          }, {
            name: 'streamPlayer',
            type: 'text',
            label: 'Stream player',
            defaultValue: 'Unibet'
          }, {
            name: 'durationStreamed',
            type: 'text',
            label: 'Duration streamed',
            defaultValue: ''
          }, {
            name: 'stake_value',
            type: 'text',
            label: 'Stake value',
            defaultValue: ''
          }]
        }, {
          name: 'type',
          type: 'text',
          label: 'Favourites: type',
          defaultValue: ''
        }, {
          name: 'name',
          type: 'text',
          label: 'Favourites: name',
          defaultValue: ''
        }]
      };
      const sportbookEvents = {
        eventName: 'sportbookEvents',
        label: 'Sportsbook event',
        fields: [{
          name: 'event',
          type: 'text',
          label: 'Kambi event (e.g. kambi page view)',
          defaultValue: 'kambi page view'
        }, {
          name: 'detail',
          type: 'object',
          label: 'Widget / navigation detail',
          fields: [{
            name: 'name',
            type: 'select',
            label: 'Name',
            options: ['widget', 'navigationBar', 'Stream widget', 'Audio commentary widget', 'search'],
            defaultValue: 'widget'
          }, {
            name: 'value',
            type: 'text',
            label: 'Value',
            defaultValue: 'football'
          }, {
            name: 'position',
            type: 'text',
            label: 'Position',
            defaultValue: '1'
          }, {
            name: 'interaction_name',
            type: 'text',
            label: 'Interaction name',
            defaultValue: 'click_through'
          }, {
            name: 'clickedElement',
            type: 'text',
            label: 'Clicked element',
            defaultValue: 'event'
          }, {
            name: 'event_type',
            type: 'text',
            label: 'Event type (e.g. livestream)',
            defaultValue: ''
          }]
        }]
      };
      const racingInteraction = {
        eventName: 'racingInteraction',
        label: 'Racing interaction',
        fields: [{
          name: 'event',
          type: 'select',
          label: 'Racing event',
          options: ['KRP add to betslip', 'KRP place bet', 'KRP Page Interaction', 'KRP page view'],
          defaultValue: 'KRP page view'
        }, {
          name: 'page',
          type: 'object',
          label: 'Page data',
          fields: [{
            name: 'path',
            type: 'text',
            label: 'Path',
            defaultValue: '/racing#/horses'
          }, {
            name: 'type',
            type: 'text',
            label: 'Type',
            defaultValue: 'home'
          }, {
            name: 'pageName',
            type: 'text',
            label: 'Page name',
            defaultValue: 'racing home'
          }, {
            name: 'isTRCAvailable',
            type: 'text',
            label: 'isTRCAvailable',
            defaultValue: 'true'
          }, {
            name: 'isLiveStreaming',
            type: 'text',
            label: 'isLiveStreaming',
            defaultValue: 'false'
          }, {
            name: 'isRadioPlaying',
            type: 'text',
            label: 'isRadioPlaying',
            defaultValue: 'false'
          }]
        }]
      };
      const promotionFields = [{
        name: 'name',
        type: 'text',
        label: 'Promotion name',
        defaultValue: 'welcome offer'
      }, {
        name: 'category',
        type: 'text',
        label: 'Category',
        defaultValue: 'sportsbook'
      }, {
        name: 'listTitle',
        type: 'text',
        label: 'List title',
        defaultValue: 'Featured'
      }, {
        name: 'listItemsNumber',
        type: 'number',
        label: 'List items number',
        defaultValue: 5
      }, {
        name: 'promotionId',
        type: 'number',
        label: 'Promotion ID',
        defaultValue: 12345
      }, {
        name: 'button',
        type: 'text',
        label: 'Button / CTA',
        defaultValue: 'opt-in'
      }];
      const promoListView = {
        eventName: 'promoListView',
        label: 'Promotion list view',
        fields: promotionFields
      };
      const promoDetailsView = {
        eventName: 'promoDetailsView',
        label: 'Promotion details view',
        fields: promotionFields
      };
      const promoDetailsAction = {
        eventName: 'promoDetailsAction',
        label: 'Promotion details action',
        fields: promotionFields
      };
      const promotionOptIn = {
        eventName: 'PromotionOptIn',
        label: 'Promotion opt-in',
        fields: promotionFields
      };
      const hamburgerMenuClick = {
        eventName: 'hamburgerMenuClick',
        label: 'Hamburger menu click',
        fields: [{
          name: 'menuClicked',
          type: 'text',
          label: 'Menu path (e.g. /betting, /casino)',
          defaultValue: '/betting'
        }]
      };
      const cashbackInteraction = {
        eventName: 'cashbackInteraction',
        label: 'Cashback interaction',
        fields: [{
          name: 'type',
          type: 'text',
          label: 'Type',
          defaultValue: 'view'
        }, {
          name: 'timestamp',
          type: 'number',
          label: 'Timestamp (stripped before Snowplow)',
          defaultValue: Date.now()
        }, {
          name: 'widget_page_url',
          type: 'text',
          label: 'Widget page URL (stripped before Snowplow)',
          defaultValue: 'https://www.unibet.com/promotions'
        }]
      };
      const depositCompleted = {
        eventName: 'depositCompleted',
        label: 'Deposit completed',
        fields: depositFields
      };
      const depositRequested = {
        eventName: 'depositRequested',
        label: 'Deposit requested',
        fields: depositFields
      };
      const modal = {
        eventName: 'modal',
        label: 'Modal',
        fields: [{
          name: 'modalCategory',
          type: 'text',
          label: 'Modal category',
          defaultValue: 'rg limits'
        }, {
          name: 'modalAction',
          type: 'text',
          label: 'Modal action (Appeared / Closed / CTAClicked)',
          defaultValue: 'CTAClicked'
        }, {
          name: 'modalSubCategory',
          type: 'text',
          label: 'Modal sub-category',
          defaultValue: ''
        }, {
          name: 'timestamp',
          type: 'number',
          label: 'Timestamp',
          defaultValue: Date.now()
        }]
      };
      const siteModal = {
        eventName: 'siteModal',
        label: 'Site modal',
        fields: [{
          name: 'modalCategory',
          type: 'text',
          label: 'Modal category',
          defaultValue: 'rg limits'
        }, {
          name: 'modalAction',
          type: 'text',
          label: 'Modal action',
          defaultValue: 'Appeared'
        }, {
          name: 'modalSubCategory',
          type: 'text',
          label: 'Modal sub-category',
          defaultValue: ''
        }, {
          name: 'timestamp',
          type: 'number',
          label: 'Timestamp',
          defaultValue: Date.now()
        }]
      };
      const personalDetailsCTAClicked = {
        eventName: 'personalDetailsCTAClicked',
        label: 'Personal details CTA clicked',
        fields: [{
          name: 'widget_name',
          type: 'text',
          label: 'Widget / activity name',
          defaultValue: 'personal details'
        }, {
          name: 'widget_cta_name',
          type: 'text',
          label: 'Widget CTA name',
          defaultValue: 'save'
        }, {
          name: 'interaction_name',
          type: 'text',
          label: 'Interaction name',
          defaultValue: 'CTAClicked'
        }, {
          name: 'interaction_type',
          type: 'text',
          label: 'Interaction type',
          defaultValue: 'popupMessageCTAClicked'
        }, {
          name: 'additionalInfo',
          type: 'text',
          label: 'Additional info',
          defaultValue: 'popumessage'
        }]
      };
      const selfassessment = {
        eventName: 'selfassessment',
        label: 'Self assessment',
        fields: [{
          name: 'interaction_name',
          type: 'text',
          label: 'Interaction name (include “completed” to fire Snowplow)',
          defaultValue: 'self test completed'
        }, {
          name: 'score',
          type: 'text',
          label: 'Score',
          defaultValue: '5'
        }]
      };
      const msgList = {
        eventName: 'msgList',
        label: 'Message center: list',
        fields: [{
          name: 'totalMsg',
          type: 'number',
          label: 'Total messages',
          defaultValue: 10
        }, {
          name: 'unreadMsg',
          type: 'number',
          label: 'Unread messages',
          defaultValue: 2
        }]
      };
      const openMsg = {
        eventName: 'openMsg',
        label: 'Message center: open',
        fields: [{
          name: 'msgId',
          type: 'text',
          label: 'Message ID',
          defaultValue: '1001'
        }, {
          name: 'subject',
          type: 'text',
          label: 'Subject',
          defaultValue: 'Welcome'
        }, {
          name: 'ctaText',
          type: 'text',
          label: 'CTA text',
          defaultValue: 'OK'
        }, {
          name: 'msgStatus',
          type: 'text',
          label: 'Message status',
          defaultValue: 'read'
        }]
      };
      const deleteMsg = {
        eventName: 'deleteMsg',
        label: 'Message center: delete',
        fields: [{
          name: 'msgId',
          type: 'text',
          label: 'Message ID',
          defaultValue: '1001'
        }, {
          name: 'msgStatus',
          type: 'text',
          label: 'Message status',
          defaultValue: 'deleted'
        }]
      };
      const promotionCTAClick = {
        eventName: 'promotionCTAClick',
        label: 'Promotion: CTA click',
        fields: promotionFields
      };
      const promotionInteraction = {
        eventName: 'promotionInteraction',
        label: 'Promotion: interaction',
        fields: [...promotionFields, {
          name: 'action',
          type: 'select',
          label: 'Action',
          options: ['click', 'view'],
          defaultValue: 'click'
        }, {
          name: 'ctaName',
          type: 'text',
          label: 'CTA name',
          defaultValue: 'opt in'
        }]
      };
      const popupmessage = {
        eventName: 'popupmessage',
        label: 'Popup message',
        fields: [{
          name: 'widget_name',
          type: 'text',
          label: 'Widget name',
          defaultValue: 'bonus offer'
        }, {
          name: 'widget_cta_name',
          type: 'text',
          label: 'Widget CTA',
          defaultValue: 'OK'
        }, {
          name: 'interaction_name',
          type: 'text',
          label: 'Interaction name',
          defaultValue: 'Appeared'
        }, {
          name: 'interaction_type',
          type: 'text',
          label: 'Interaction type',
          defaultValue: 'popupMessageCTAClicked'
        }, {
          name: 'additionalInfo',
          type: 'text',
          label: 'Additional info',
          defaultValue: 'popumessage'
        }]
      };
      const gameLaunch = {
        eventName: 'gameLaunch',
        label: 'Casino: game launch',
        fields: [{
          name: 'gameName',
          type: 'text',
          label: 'Game name',
          defaultValue: 'Starburst'
        }, {
          name: 'gameId',
          type: 'text',
          label: 'Game ID',
          defaultValue: 'starburst'
        }, {
          name: 'uniquegameId',
          type: 'text',
          label: 'Unique game ID',
          defaultValue: 'starburst'
        }, {
          name: 'source',
          type: 'text',
          label: 'Launch source',
          defaultValue: 'direct'
        }, {
          name: 'isPlayForFun',
          type: 'boolean',
          label: 'Play for fun',
          defaultValue: false
        }, {
          name: 'realMoneyMode',
          type: 'text',
          label: 'Real money mode',
          defaultValue: ''
        }, {
          name: 'launchElementPosition',
          type: 'number',
          label: 'Launch element position',
          defaultValue: 1
        }, {
          name: 'launchListPosition',
          type: 'number',
          label: 'Launch list position',
          defaultValue: 1
        }, {
          name: 'keywords',
          type: 'text',
          label: 'Keywords',
          defaultValue: ''
        }, {
          name: 'referrerPathname',
          type: 'text',
          label: 'Referrer path',
          defaultValue: '/casino'
        }, {
          name: 'product',
          type: 'text',
          label: 'Product',
          defaultValue: 'casino'
        }, {
          name: 'sortingMethod',
          type: 'text',
          label: 'Sorting method',
          defaultValue: ''
        }]
      };
      const gameNavigation$1 = {
        eventName: 'gameNavigation',
        label: 'Casino: game navigation',
        fields: [{
          name: 'action',
          type: 'select',
          label: 'Action',
          options: ['click', 'hover', 'view'],
          defaultValue: 'click'
        }, {
          name: 'navigation_id',
          type: 'text',
          label: 'Navigation ID',
          defaultValue: 'slots'
        }, {
          name: 'section',
          type: 'text',
          label: 'Section',
          defaultValue: 'lobby'
        }, {
          name: 'position',
          type: 'text',
          label: 'Position',
          defaultValue: '1'
        }]
      };
      const gamingWidgetInteraction$1 = {
        eventName: 'gamingWidgetInteraction',
        label: 'Casino: gaming widget',
        fields: [{
          name: 'action',
          type: 'text',
          label: 'Action',
          defaultValue: 'click'
        }, {
          name: 'userViewCount',
          type: 'number',
          label: 'User view count',
          defaultValue: 1
        }, {
          name: 'ctaClicked',
          type: 'text',
          label: 'CTA clicked',
          defaultValue: 'play'
        }, {
          name: 'container',
          type: 'text',
          label: 'Container',
          defaultValue: 'home'
        }, {
          name: 'widgetType',
          type: 'select',
          label: 'Widget type',
          options: ['game', 'tournament'],
          defaultValue: 'game'
        }, {
          name: 'widgetDetails',
          type: 'object',
          label: 'Widget details',
          fields: [{
            name: 'id',
            type: 'text',
            label: 'ID',
            defaultValue: '123'
          }, {
            name: 'name',
            type: 'text',
            label: 'Name',
            defaultValue: 'Book of Dead'
          }, {
            name: 'status',
            type: 'select',
            label: 'Status (tournament)',
            options: ['active', 'upcoming', 'finished'],
            defaultValue: 'active'
          }, {
            name: 'productType',
            type: 'text',
            label: 'Product type',
            defaultValue: 'casino'
          }]
        }, {
          name: 'elementPosition',
          type: 'number',
          label: 'Element position',
          defaultValue: 1
        }, {
          name: 'tournamentPosition',
          type: 'number',
          label: 'Tournament position',
          defaultValue: 1
        }, {
          name: 'gamesIdsInTournament',
          type: 'text',
          label: 'Game IDs in tournament',
          defaultValue: ''
        }, {
          name: 'gamesNamesInTournament',
          type: 'text',
          label: 'Game names in tournament',
          defaultValue: ''
        }]
      };
      const gameSearchModule$1 = {
        eventName: 'gameSearchModule',
        label: 'Casino: game search',
        fields: [{
          name: 'searchTerm',
          type: 'text',
          label: 'Search term',
          defaultValue: 'book'
        }, {
          name: 'searchStatus',
          type: 'select',
          label: 'Search status',
          options: ['searchSuccess', 'searchNoResults', 'searchStart'],
          defaultValue: 'searchSuccess'
        }, {
          name: 'numOfReturnedGames',
          type: 'number',
          label: 'Number of results',
          defaultValue: 5
        }, {
          name: 'topFiveResults',
          type: 'text',
          label: 'Top results',
          defaultValue: ''
        }]
      };
      const gameMenuInteraction$1 = {
        eventName: 'gameMenuInteraction',
        label: 'Casino: in-game menu',
        fields: [{
          name: 'type',
          type: 'text',
          label: 'Type',
          defaultValue: 'menu interaction'
        }, {
          name: 'label',
          type: 'text',
          label: 'Menu label',
          defaultValue: 'close_game'
        }]
      };
      const globalJackpotInteraction = {
        eventName: 'globalJackpotInteraction',
        label: 'Casino: global jackpot',
        fields: [{
          name: 'source',
          type: 'text',
          label: 'Source',
          defaultValue: 'header'
        }, {
          name: 'container',
          type: 'text',
          label: 'Container',
          defaultValue: 'lobby'
        }, {
          name: 'action',
          type: 'text',
          label: 'Action',
          defaultValue: 'click'
        }]
      };
      const nextGameInteraction$1 = {
        eventName: 'nextGameInteraction',
        label: 'Casino: next game',
        fields: [{
          name: 'type',
          type: 'text',
          label: 'Type',
          defaultValue: 'next'
        }, {
          name: 'container',
          type: 'text',
          label: 'Container',
          defaultValue: 'recommendations'
        }, {
          name: 'casinoGameId',
          type: 'text',
          label: 'Casino game ID',
          defaultValue: '100'
        }, {
          name: 'position',
          type: 'number',
          label: 'Position',
          defaultValue: 1
        }]
      };
      const pokerInteraction = {
        eventName: 'pokerInteraction',
        label: 'Poker interaction',
        fields: [{
          name: 'action',
          type: 'text',
          label: 'Action',
          defaultValue: 'click'
        }, {
          name: 'container',
          type: 'text',
          label: 'Container',
          defaultValue: 'lobby'
        }, {
          name: 'contentBlockName',
          type: 'text',
          label: 'Content block name',
          defaultValue: 'promo'
        }, {
          name: 'contentBlockOrder',
          type: 'number',
          label: 'Content block order',
          defaultValue: 1
        }, {
          name: 'name',
          type: 'text',
          label: 'Name',
          defaultValue: 'tournament'
        }]
      };
      const postLoginInteraction = {
        eventName: 'post_login_interaction',
        label: 'Post-login interaction',
        fields: [{
          name: 'event_type',
          type: 'select',
          label: 'Event type',
          options: ['step_view', 'journey_complete', 'browser_close'],
          defaultValue: 'step_view'
        }, {
          name: 'step_number',
          type: 'number',
          label: 'Step number',
          defaultValue: 1
        }, {
          name: 'step_name',
          type: 'text',
          label: 'Step name',
          defaultValue: 'verify_email'
        }, {
          name: 'expected_step_count',
          type: 'number',
          label: 'Expected step count',
          defaultValue: 3
        }, {
          name: 'should_show',
          type: 'boolean',
          label: 'Should show',
          defaultValue: true
        }, {
          name: 'timestamp',
          type: 'number',
          label: 'Timestamp',
          defaultValue: Date.now()
        }]
      };
      const loginSuccess = {
        eventName: 'loginSuccess',
        label: 'Login: success',
        fields: [{
          name: 'login_method',
          type: 'text',
          label: 'Login method',
          defaultValue: 'password'
        }, {
          name: 'widget_name',
          type: 'text',
          label: 'Widget name',
          defaultValue: 'Login'
        }, {
          name: 'widget_cta_name',
          type: 'text',
          label: 'CTA',
          defaultValue: 'submit'
        }, {
          name: 'userId',
          type: 'number',
          label: 'User ID',
          defaultValue: 100000000
        }]
      };
      const loginminiAppError = {
        eventName: 'loginminiAppError',
        label: 'Login: error',
        fields: [{
          name: 'login_method',
          type: 'text',
          label: 'Login method',
          defaultValue: 'password'
        }, {
          name: 'widget_name',
          type: 'text',
          label: 'Widget name',
          defaultValue: 'Login'
        }, {
          name: 'errorCode',
          type: 'text',
          label: 'Error code',
          defaultValue: 'invalid_credentials'
        }, {
          name: 'errorMessage',
          type: 'text',
          label: 'Error message',
          defaultValue: 'Invalid credentials'
        }]
      };
      const loginminiAppPopupAppeared = {
        eventName: 'loginminiAppPopupAppeared',
        label: 'Login: popup appeared',
        fields: [{
          name: 'interaction_name',
          type: 'text',
          label: 'Interaction name',
          defaultValue: 'Appeared'
        }, {
          name: 'widget_name',
          type: 'text',
          label: 'Widget name',
          defaultValue: 'Login Pop-up'
        }, {
          name: 'widget_cta_name',
          type: 'text',
          label: 'CTA',
          defaultValue: ''
        }]
      };
      const loginminiAppPopupClosed = {
        eventName: 'loginminiAppPopupClosed',
        label: 'Login: popup closed',
        fields: [{
          name: 'interaction_name',
          type: 'text',
          label: 'Interaction name',
          defaultValue: 'loginminiAppPopupClosed'
        }, {
          name: 'widget_name',
          type: 'text',
          label: 'Widget name',
          defaultValue: 'Login Pop-up'
        }]
      };
      const loginminiAPPPopUpInteraction = {
        eventName: 'loginminiAPPPopUpInteraction',
        label: 'Login: popup CTA',
        fields: [{
          name: 'interaction_name',
          type: 'text',
          label: 'Interaction name',
          defaultValue: 'loginminiAPPPopUpInteraction'
        }, {
          name: 'widget_name',
          type: 'text',
          label: 'Widget name',
          defaultValue: 'Login Pop-up'
        }, {
          name: 'widget_cta_name',
          type: 'text',
          label: 'CTA',
          defaultValue: 'Login'
        }]
      };
      const passwordResetSubmit = {
        eventName: 'passwordResetSubmit',
        label: 'Login: password reset submit',
        fields: [{
          name: 'login_method',
          type: 'text',
          label: 'Login method',
          defaultValue: ''
        }, {
          name: 'widget_name',
          type: 'text',
          label: 'Widget name',
          defaultValue: 'Reset Submit'
        }, {
          name: 'widget_cta_name',
          type: 'text',
          label: 'CTA',
          defaultValue: 'CTAClicked'
        }]
      };
      const controlsAndLimits = {
        eventName: 'controls_and_limits',
        label: 'Controls & limits',
        fields: [{
          name: 'control_event',
          type: 'text',
          label: 'Control event',
          defaultValue: 'deposit limit'
        }, {
          name: 'limit_type',
          type: 'text',
          label: 'Limit type',
          defaultValue: 'deposit'
        }, {
          name: 'limit_subtype',
          type: 'text',
          label: 'Limit subtype',
          defaultValue: 'daily'
        }, {
          name: 'limit_value',
          type: 'text',
          label: 'Limit value',
          defaultValue: '100'
        }, {
          name: 'limit_timeframe',
          type: 'text',
          label: 'Limit timeframe',
          defaultValue: '24h'
        }, {
          name: 'limit_product',
          type: 'text',
          label: 'Product',
          defaultValue: 'sportsbook'
        }, {
          name: 'interaction_name',
          type: 'text',
          label: 'Interaction name',
          defaultValue: ''
        }, {
          name: 'type',
          type: 'text',
          label: 'Type',
          defaultValue: ''
        }]
      };
      const kmfVerificationEvent = {
        eventName: 'kmf_verification_event',
        label: 'KMF verification',
        fields: [{
          name: 'event_category',
          type: 'text',
          label: 'Event category',
          defaultValue: 'document_upload'
        }, {
          name: 'event_sub_category',
          type: 'text',
          label: 'Document type',
          defaultValue: 'passport'
        }, {
          name: 'verification_type',
          type: 'text',
          label: 'Verification type',
          defaultValue: 'idv'
        }, {
          name: 'verification_process',
          type: 'text',
          label: 'Verification process',
          defaultValue: 'standard'
        }, {
          name: 'view_category',
          type: 'text',
          label: 'View category',
          defaultValue: 'verification'
        }, {
          name: 'provider_name',
          type: 'text',
          label: 'Provider name',
          defaultValue: ''
        }, {
          name: 'documentUploadStatus',
          type: 'text',
          label: 'Document upload status',
          defaultValue: 'success'
        }, {
          name: 'error_message',
          type: 'text',
          label: 'Error message (optional)',
          defaultValue: ''
        }]
      };
      const channelVerificationInteraction = {
        eventName: 'channel_verification_interaction',
        label: 'Channel verification',
        fields: [{
          name: 'verification_method',
          type: 'text',
          label: 'Verification method',
          defaultValue: 'sms'
        }, {
          name: 'interaction',
          type: 'text',
          label: 'Interaction',
          defaultValue: 'clickCTA'
        }, {
          name: 'screen_name',
          type: 'text',
          label: 'Screen name',
          defaultValue: 'verify_phone'
        }, {
          name: 'click_element_name',
          type: 'text',
          label: 'Click element name',
          defaultValue: 'verify_now'
        }]
      };
      const bonusFields = [{
        name: 'bonusId',
        type: 'number',
        label: 'Bonus ID',
        defaultValue: 1
      }, {
        name: 'id',
        type: 'number',
        label: 'Campaign ID',
        defaultValue: 1
      }, {
        name: 'name',
        type: 'text',
        label: 'Name',
        defaultValue: 'Welcome bonus'
      }, {
        name: 'bonusOfferType',
        type: 'text',
        label: 'Bonus offer type',
        defaultValue: 'casino'
      }, {
        name: 'message',
        type: 'text',
        label: 'Error message (bonusError)',
        defaultValue: ''
      }];
      const bonusAccept = {
        eventName: 'bonusAccept',
        label: 'Bonus: accept',
        fields: bonusFields
      };
      const bonusAccepted = {
        eventName: 'bonusAccepted',
        label: 'Bonus: accepted',
        fields: bonusFields
      };
      const bonusView = {
        eventName: 'bonusView',
        label: 'Bonus: view',
        fields: bonusFields
      };
      const bonusError = {
        eventName: 'bonusError',
        label: 'Bonus: error',
        fields: bonusFields
      };
      const tournamentFields = [{
        name: 'tournamentId',
        type: 'number',
        label: 'Tournament ID',
        defaultValue: 1
      }, {
        name: 'tournamentName',
        type: 'text',
        label: 'Tournament name',
        defaultValue: 'Weekly race'
      }, {
        name: 'tournamentStartDate',
        type: 'text',
        label: 'Start date',
        defaultValue: '2025-01-01'
      }, {
        name: 'tournamentEndsIn',
        type: 'text',
        label: 'Ends in',
        defaultValue: '2d'
      }, {
        name: 'status',
        type: 'select',
        label: 'Status',
        options: ['active', 'upcoming', 'finished'],
        defaultValue: 'active'
      }, {
        name: 'gamesInTournament',
        type: 'text',
        label: 'Games in tournament',
        defaultValue: ''
      }, {
        name: 'gamesNamesInTournament',
        type: 'text',
        label: 'Game names',
        defaultValue: ''
      }, {
        name: 'tournLocation',
        type: 'text',
        label: 'Location',
        defaultValue: 'casino lobby'
      }, {
        name: 'elementPosition',
        type: 'string',
        label: 'Element position',
        defaultValue: '1'
      }, {
        name: 'tournamentPosition',
        type: 'number',
        label: 'Tournament position',
        defaultValue: 1
      }];
      const tournamentOptIn = {
        eventName: 'tournamentOptIn',
        label: 'Tournament: opt in',
        fields: tournamentFields
      };
      const tournamentView = {
        eventName: 'tournamentView',
        label: 'Tournament: view',
        fields: tournamentFields
      };
      const experimentActivated = {
        eventName: 'experimentActivated',
        label: 'Experiment activated',
        fields: [{
          name: 'experimentName',
          type: 'text',
          label: 'Experiment name (ruleKey)',
          defaultValue: 'my_experiment'
        }, {
          name: 'variationKey',
          type: 'text',
          label: 'Variation key',
          defaultValue: 'variant_a'
        }, {
          name: 'variationId',
          type: 'text',
          label: 'Variation ID',
          defaultValue: '1'
        }, {
          name: 'experiment',
          type: 'object',
          label: 'Experiment',
          fields: [{
            name: 'key',
            type: 'text',
            label: 'Experiment key',
            defaultValue: 'my_experiment'
          }]
        }, {
          name: 'result',
          type: 'object',
          label: 'Result',
          fields: [{
            name: 'variationId',
            type: 'text',
            label: 'Variation ID',
            defaultValue: '1'
          }]
        }]
      };
      const genericInteraction = {
        eventName: 'genericInteraction',
        label: 'Generic interaction',
        fields: [{
          name: 'type',
          type: 'text',
          label: 'Type',
          defaultValue: 'banner click'
        }, {
          name: 'value',
          type: 'text',
          label: 'Value',
          defaultValue: 'home hero'
        }, {
          name: 'additionalInfo',
          type: 'text',
          label: 'Additional info',
          defaultValue: ''
        }, {
          name: 'track_link_name',
          type: 'text',
          label: 'Track link name (alternate shape)',
          defaultValue: ''
        }]
      };
      const genericBannerInteraction = {
        eventName: 'genericBannerInteraction',
        label: 'Banner interaction',
        fields: [{
          name: 'action',
          type: 'text',
          label: 'Action',
          defaultValue: 'click'
        }, {
          name: 'value',
          type: 'text',
          label: 'Value (with click)',
          defaultValue: 'cta'
        }, {
          name: 'product',
          type: 'text',
          label: 'Product',
          defaultValue: 'casino'
        }, {
          name: 'header',
          type: 'text',
          label: 'Header',
          defaultValue: 'Promo'
        }, {
          name: 'container',
          type: 'text',
          label: 'Container',
          defaultValue: 'home'
        }]
      };
      const paymentUserEvent = {
        eventName: 'paymentUserEvent',
        label: 'Payment user event',
        fields: [{
          name: 'methodKey',
          type: 'text',
          label: 'Method key',
          defaultValue: 'card'
        }, {
          name: 'method',
          type: 'text',
          label: 'Method',
          defaultValue: 'visa'
        }, {
          name: 'transactionRef',
          type: 'text',
          label: 'Transaction ref',
          defaultValue: 'tx-1'
        }, {
          name: 'eventType',
          type: 'text',
          label: 'Event type',
          defaultValue: 'add'
        }, {
          name: 'target',
          type: 'text',
          label: 'Target',
          defaultValue: 'wallet'
        }, {
          name: 'values',
          type: 'text',
          label: 'Values',
          defaultValue: ''
        }, {
          name: 'siteSection',
          type: 'text',
          label: 'Site section',
          defaultValue: 'cashier'
        }]
      };
      const installationInteraction = {
        eventName: 'installationInteraction',
        label: 'App installation',
        fields: [{
          name: 'step',
          type: 'text',
          label: 'Step',
          defaultValue: 'download'
        }, {
          name: 'location',
          type: 'text',
          label: 'Location',
          defaultValue: 'footer'
        }, {
          name: 'iOS_default',
          type: 'boolean',
          label: 'iOS default',
          defaultValue: false
        }]
      };
      const offlineInteraction = {
        eventName: 'offlineInteraction',
        label: 'Offline interaction',
        fields: [{
          name: 'type',
          type: 'select',
          label: 'Type',
          options: ['online_triggered', 'offline_view', 'sync'],
          defaultValue: 'online_triggered'
        }, {
          name: 'screenType',
          type: 'text',
          label: 'Screen type',
          defaultValue: 'queue'
        }]
      };
      const notificationInteraction = {
        eventName: 'notificationInteraction',
        label: 'Notifications',
        fields: [{
          name: 'interaction',
          type: 'text',
          label: 'Interaction',
          defaultValue: 'open'
        }, {
          name: 'type',
          type: 'text',
          label: 'Type',
          defaultValue: 'promo'
        }, {
          name: 'title',
          type: 'text',
          label: 'Title',
          defaultValue: 'Offer'
        }, {
          name: 'filter',
          type: 'text',
          label: 'Filter',
          defaultValue: ''
        }, {
          name: 'cta_name',
          type: 'text',
          label: 'CTA name',
          defaultValue: 'view'
        }]
      };
      const helpCentreInteraction = {
        eventName: 'help_centre_interaction',
        label: 'Help centre interaction',
        fields: [{
          name: 'interaction_name',
          type: 'select',
          label: 'Interaction name',
          options: ['click', 'search', 'pageview'],
          defaultValue: 'click'
        }, {
          name: 'category_id',
          type: 'text',
          label: 'Category ID',
          defaultValue: ''
        }, {
          name: 'widget',
          type: 'text',
          label: 'Widget',
          defaultValue: ''
        }, {
          name: 'channel',
          type: 'text',
          label: 'Channel',
          defaultValue: 'email'
        }, {
          name: 'answer_id',
          type: 'text',
          label: 'Answer ID',
          defaultValue: ''
        }, {
          name: 'product_id',
          type: 'text',
          label: 'Product ID',
          defaultValue: 'sportsbook'
        }, {
          name: 'article_id',
          type: 'text',
          label: 'Article ID',
          defaultValue: ''
        }, {
          name: 'article_rating',
          type: 'text',
          label: 'Article rating',
          defaultValue: ''
        }, {
          name: 'search_data',
          type: 'object',
          label: 'Search data',
          fields: [{
            name: 'keyword',
            type: 'text',
            label: 'Keyword',
            defaultValue: 'deposit'
          }, {
            name: 'number_of_results',
            type: 'number',
            label: 'Number of results',
            defaultValue: 5
          }, {
            name: 'top_results',
            type: 'text',
            label: 'Top results',
            defaultValue: ''
          }]
        }]
      };
      const registrationEvent = {
        eventName: 'registrationInteraction',
        label: 'Registration Event',
        fields: [{
          name: 'name',
          type: 'select',
          label: 'Step Name',
          defaultValue: 'step_one',
          options: ['step_one', 'step_two', 'step_three', 'step_four', 'welcome_bonus_step', 'registration_type_selected', 'registration_successful', 'registration_error']
        }, {
          name: 'method',
          type: 'select',
          label: 'Registration Method',
          defaultValue: 'manual',
          options: ['manual', 'eauth_itsme', 'eauth_tupas', 'eauth_criipto', 'eauth_bankid', 'fast_lane']
        }, {
          name: 'order',
          type: 'number',
          label: 'Step Order',
          min: 1,
          max: 10,
          defaultValue: 1
        }, {
          name: 'processId',
          type: 'text',
          label: 'Process ID',
          defaultValue: 'analytics_testing_1234'
        }, {
          name: 'communicationSelected',
          type: 'array',
          label: 'Communication selected',
          options: ['email', 'sms', 'push'],
          defaultValue: []
        }, {
          name: 'customerId',
          type: 'number',
          label: 'Customer ID',
          defaultValue: 100000000,
          max: 999999999
        }, {
          name: 'deposit',
          type: 'object',
          label: 'deposit',
          fields: [{
            name: 'type',
            type: 'text',
            label: 'Type',
            defaultValue: 'success'
          }, {
            name: 'count',
            type: 'number',
            label: 'Count',
            defaultValue: 1
          }, {
            name: 'amount',
            type: 'number',
            label: 'Amount',
            defaultValue: 100
          }, {
            name: 'method',
            type: 'text',
            label: 'Method',
            defaultValue: 'card'
          }, {
            name: 'currency',
            type: 'text',
            label: 'Currency',
            defaultValue: 'EUR'
          }, {
            name: 'id',
            type: 'text',
            label: 'ID',
            defaultValue: '1234567890'
          }]
        }, {
          name: 'controls_and_limits',
          type: 'array',
          label: 'Controls & limits',
          items: [{
            name: 'type',
            type: 'text',
            label: 'Type',
            defaultValue: 'limit applied'
          }, {
            name: 'limit_type',
            type: 'text',
            label: 'Limit type',
            defaultValue: 'deposit_limit'
          }, {
            name: 'limit_subtype',
            type: 'text',
            label: 'Limit subtype',
            defaultValue: 'mandatory_deposit_limit'
          }, {
            name: 'value',
            type: 'number',
            label: 'Limit value',
            defaultValue: 100
          }, {
            name: 'timeframe',
            type: 'text',
            label: 'Limit timeframe',
            defaultValue: 'DAILY'
          }, {
            name: 'product',
            type: 'text',
            label: 'Product',
            defaultValue: null
          }]
        }
        /*{
            name: 'verification',
            type: 'object',
            label: 'Verification',
            fields: kmfVerificationEvent.fields,
        }*/]
      };

      /** Dev-tools form schema for one field (object/array types may nest `fields` / `items`). */

      const eventCategories = () => [{
        key: 'bonus',
        label: 'Bonus',
        events: [bonusAccept, bonusAccepted, bonusView, bonusError]
      }, {
        key: 'sportsbook',
        label: 'Sportsbook & racing',
        events: [kspEvent, sportbookEvents, racingInteraction]
      }, {
        key: 'registration',
        label: 'Registration',
        events: [registrationEvent]
      }, {
        key: 'promotions',
        label: 'Promotions',
        events: [promoListView, promoDetailsView, promoDetailsAction, promotionOptIn, promotionCTAClick, promotionInteraction]
      }, {
        key: 'navigation',
        label: 'Navigation & shell',
        events: [hamburgerMenuClick, genericInteraction, genericBannerInteraction, experimentActivated]
      }, {
        key: 'payments',
        label: 'Cashback & payments',
        events: [cashbackInteraction, depositCompleted, depositRequested, paymentUserEvent]
      }, {
        key: 'modals',
        label: 'Modals & popups',
        events: [modal, siteModal, personalDetailsCTAClicked, popupmessage]
      }, {
        key: 'rg',
        label: 'Responsible gaming',
        events: [selfassessment, controlsAndLimits]
      }, {
        key: 'messages',
        label: 'Message center',
        events: [msgList, openMsg, deleteMsg]
      }, {
        key: 'casino',
        label: 'Casino & games',
        events: [gameLaunch, gameNavigation$1, gamingWidgetInteraction$1, gameSearchModule$1, gameMenuInteraction$1, globalJackpotInteraction, nextGameInteraction$1, pokerInteraction]
      }, {
        key: 'login',
        label: 'Login & post-login',
        events: [postLoginInteraction, loginSuccess, loginminiAppError, loginminiAppPopupAppeared, loginminiAppPopupClosed, loginminiAPPPopUpInteraction, passwordResetSubmit]
      }, {
        key: 'verification',
        label: 'Verification',
        events: [kmfVerificationEvent, channelVerificationInteraction]
      }, {
        key: 'tournaments',
        label: 'Tournaments',
        events: [tournamentOptIn, tournamentView]
      }, {
        key: 'platform',
        label: 'App & platform',
        events: [installationInteraction, offlineInteraction, notificationInteraction, helpCentreInteraction]
      }];

      const useDataLayer = exports('u', () => {
        var _getSitedefinition, _ref, _analyticsHelpers$sto;
        const {
          isLoggedIn,
          session
        } = useLoginState();
        const {
          customerId,
          preferredCurrency
        } = session || {};
        const {
          applicationId,
          clientId,
          currency,
          deviceGroup,
          jurisdiction,
          locale,
          translationLocale,
          channel,
          isApp,
          isKwp
        } = getSitedefinition();
        let brand = ((_getSitedefinition = getSitedefinition()) === null || _getSitedefinition === void 0 ? void 0 : _getSitedefinition.brand) || "";
        let market = jurisdiction.toLowerCase();
        if (market === 'mt') {
          if (document.location.hostname.split('.').length === 3 && /(www|en)(-(qa1|si1|pt1))?/.test(document.location.hostname.split('.')[0]) && document.location.hostname.split('.')[2] === 'com') {
            if (brand === 'kolikkopelit' || brand === 'ottokasino' || brand === 'huone') {
              if (/(www)(-(qa1|si1|pt1))?/.test(document.location.hostname.split('.')[0])) {
                market = 'fi';
              } else {
                market = 'int';
              }
            } else {
              market = 'int';
            }
          } else if (document.location.hostname.split('.')[2] !== 'mt') {
            market = locale.split('_')[1].toLowerCase();
          }
        }
        const oddsFormat = ((_ref = ((_analyticsHelpers$sto = analyticsHelpers.storageManagement._getStorage("localStorage", "key_user_setting")) === null || _analyticsHelpers$sto === void 0 ? void 0 : _analyticsHelpers$sto.oddsFormat) || analyticsHelpers.storageManagement._getStorage("localStorage", "ksp_oddsformat") || '') === null || _ref === void 0 ? void 0 : _ref.toLowerCase()) || '';
        if (brand === 'bingo_com') {
          brand = 'bingo';
        }
        return {
          applicationId,
          brand,
          clientId,
          currency,
          deviceGroup,
          jurisdiction: jurisdiction.toLowerCase(),
          locale: locale.toLowerCase(),
          translationLocale: translationLocale.toLowerCase(),
          channel,
          isApp,
          customerId,
          isLoggedIn,
          preferredCurrency,
          market: market.toLowerCase(),
          isKwp,
          oddsFormat
        };
      });
      const getCustomerId = function () {
        var _data$detail;
        let data = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : {};
        const {
          customerId
        } = useDataLayer();
        let userId = (data === null || data === void 0 ? void 0 : data.userId) || (data === null || data === void 0 ? void 0 : data.customerId) || (data === null || data === void 0 ? void 0 : (_data$detail = data.detail) === null || _data$detail === void 0 ? void 0 : _data$detail.userId) || customerId || 0;
        if (!isNaN(userId)) userId = parseInt(userId);
        if (userId === "undefined") userId = 0;
        return userId;
      };

      const getMarketingConsent = exports('b', () => {
        let consentClosed = analyticsHelpers.getCookie('OptanonAlertBoxClosed');
        let marketingConsent = false;
        if (consentClosed) {
          let OneTrustConsent = decodeURIComponent(analyticsHelpers.getCookie('OptanonConsent')) || '';
          if (OneTrustConsent.includes('C0004:1')) {
            marketingConsent = true;
          }
        } else {
          marketingConsent = null;
        }
        return marketingConsent;
      });
      const getTrackingCode = () => {
        const url = window.location.href;
        let campaignTrackingCode = '';
        const getQueryString = field => {
          const reg = new RegExp('[?&]' + field + '=([^&#]*)', 'i');
          const string = reg.exec(url);
          return string ? string[1] : null;
        };
        const isReferrerPopunder = document.referrer.indexOf('/pop/') > -1 ? true : false;
        const isMktid = url.indexOf('mktid') > -1 ? true : false;
        const isCid = url.indexOf('cid') > -1 ? true : false;
        const isUtm = url.indexOf('utm_medium') > -1 ? true : false;
        if (isMktid) {
          campaignTrackingCode = getQueryString('mktid');
        } else if (isCid) {
          campaignTrackingCode = getQueryString('cid');
        } else if (isUtm) {
          const medium = getQueryString('utm_medium');
          const source = getQueryString('utm_source') || 'NONE';
          const content = getQueryString('utm_content') || 'NONE';
          const campaign = getQueryString('utm_campaign') || 'NONE';
          const term = getQueryString('utm_term') || 'NONE';
          campaignTrackingCode = medium + ':' + source + ':' + content + ':' + campaign + ':' + term;
        }
        if (isReferrerPopunder) {
          const referrerUrl = document.referrer;
          const isReferrerMktid = referrerUrl.indexOf('mktid') > -1 ? true : false;
          const isReferrerCid = referrerUrl.indexOf('cid') > -1 ? true : false;
          if (isReferrerMktid) {
            campaignTrackingCode = getQueryString('mktid').replace('1:', 'popunder:');
          } else if (isReferrerCid) {
            campaignTrackingCode = getQueryString('cid').replace('1:', 'popunder:');
          }
        }
        return decodeURIComponent(campaignTrackingCode);
      };
      const getMarketingVariablesFromCookie = () => {
        // read the BSTAN paramaters from a cookie (jira ticket WARP-6522)
        const cookies = document.cookie.split(';').filter(c => c.trim().startsWith('affiliate_params='));
        let cookieValue;
        for (let i = 0; i < cookies.length; i++) {
          if (cookies[i].split('=')[1].includes('btag')) {
            cookieValue = cookies[i].split('=')[1];
          }
        }
        if (!cookieValue) {
          return null;
        }
        let parsedObject = null;
        try {
          parsedObject = JSON.parse(cookieValue);
        } catch (e) {}
        if (!parsedObject) {
          return null;
        }
        const searchString = Object.keys(parsedObject).map(key => `${encodeURIComponent(key)}=${encodeURIComponent(parsedObject[key])}`).join('&');
        return searchString.toLowerCase();
      };
      const marketingMap = async () => {
        try {
          var _module$default, _module$default$brand;
          let module$1;
          let brand = useDataLayer().brand;
          if (brand === "unibetsports" || brand === "unibetgames" || brand === "unibetcasino") {
            brand = "unibet";
          } else if (brand === "ottokasino" || brand === "ottocasino") {
            brand = "otto";
          } else if (brand === "vladkazino" || brand === "vladcazino") {
            brand = "vlad";
          } else if (brand === "32rosu") {
            brand = "32red";
          }
          let market = useDataLayer().market;
          if (market === 'be' && brand === 'unibet') {
            let locale = useDataLayer().locale;
            market = locale.toLowerCase();
          }
          switch (brand) {
            case '32red':
              module$1 = await module.import('./32red-2f4bfeab.js');
              break;
            case 'bingo':
              module$1 = await module.import('./bingo-09d63ab1.js');
              break;
            case 'highroller':
              module$1 = await module.import('./highroller-5ba884c4.js');
              break;
            case 'huone':
              module$1 = await module.import('./huone-38d80e55.js');
              break;
            case 'kolikkopelit':
              module$1 = await module.import('./kolikkopelit-615e2b66.js');
              break;
            case 'maria':
              module$1 = await module.import('./maria-f3a40d45.js');
              break;
            case 'otto':
              module$1 = await module.import('./otto-9b4d8ec5.js');
              break;
            case 'storspelare':
              //file may not be needed, populate as highroller
              module$1 = await module.import('./storspelare-8139c998.js');
              break;
            case 'unibet':
              module$1 = await module.import('./unibet-aac20c74.js');
              break;
            case 'vlad':
              module$1 = await module.import('./vlad-1ca25ea0.js');
              break;
            default:
              return {};
          }
          // Each brand's mapping is default export, with key as brand, then key as country
          return ((_module$default = module$1.default) === null || _module$default === void 0 ? void 0 : (_module$default$brand = _module$default[brand]) === null || _module$default$brand === void 0 ? void 0 : _module$default$brand[market]) || {};
        } catch (error) {
          // Return empty mapping or handle error gracefully
          return {};
        }
      };
      const marketingData = () => {
        const AFFILIATE = 'affiliate';
        const NATURAL_SEARCH = 'natural_search';
        const NATURAL_SOCIAL = 'natural_social';
        const REFERRING_DOMAIN = 'referring_domains';
        const SATELLITE_SITE = 'satellite_site';
        // Only domains present in the lists will activate their respective channels
        const DOMAINS_NATURAL_SEARCH = ['www.google.', 'bing.', 'search.yahoo.', 'search.seznam.', '.yandex.', '.ask.'];
        const DOMAINS_NATURAL_SOCIAL = ['facebook.com', 't.co', 'pinterest.', 'linked.com', 'plus.google', 'instagram.com', 'hootsuite.com'];
        // Exclusion list: domains that are considered internal
        let DOMAINS_REFERRING = ['.unibet.', '.bingo.', '.vladcazino.', '.highroller.', '.highrolling.', '.storspelare.', '.storspiller.', '.igame.', '.casinohuone.', '.kolikkopelit.', '.mariacasino.', 'paypal.com', 'merchant.itsme', '.32red.', '.ottokasino', '.ottocasino.'];
        const IDIN_DOMAINS = ['diensten.snsbank.nl', '.abnamro.nl', 'diensten.asnbank.nl', 'idin.bunq.com', 'ideal.ing.nl', 'idp.rabobank.nl', 'diensten.regiobank.nl', 'diensten.snsbank.nl'];
        const METID_NEMID = ['unibet.criipto.id', 'unibet.mitid.dk'];
        DOMAINS_REFERRING = DOMAINS_REFERRING.concat(IDIN_DOMAINS).concat(METID_NEMID);
        let marketingData = {};
        const getMarketingData = () => {
          const OLD_TRACKING_CODE = getTrackingCode();
          // URLSearchParams interface : https://developer.mozilla.org/en-US/docs/Web/API/URLSearchParams
          // URL query parameters names are lower-cased to avoid issues with capitalization
          let sanited_search = window.location.search;
          if (sanited_search === '') {
            sanited_search = analyticsHelpers.getCookie('queryString');
          } else {
            sanited_search = sanited_search.replace(/([^&?\/=]*)=/gi, x => x.toLowerCase());
          }
          if (sanited_search === '') sanited_search = getMarketingVariablesFromCookie();
          const paramsObj = new URLSearchParams(sanited_search);
          const referrer = document.referrer;
          let marketingChannelId, marketingSubChannelId;
          const getDomainFromUrl = str => {
            if (str && str !== '') {
              const tmpUrl = new URL(str);
              return tmpUrl.hostname;
            }
          };
          const identifyChannels = (channelId, channelDomainMapping, referrer) => {
            /* identifyChannels
             ** Returns an array with [channel_id, sub_channel]
             */
            if (referrer && referrer !== '') {
              var refDomain = getDomainFromUrl(referrer);
              var currDomain = window.location.hostname;
              if (channelId === REFERRING_DOMAIN) {
                /*
                 **  Referring domain checks:
                 **  1. Referring domain present
                 **  2. Referring domain different than current domain
                 **  3. Referring domain different than the DOMAINS_REFERRING check list
                 */
                // Current referrer should not contain any of the domains in the domain mapping.
                if (currDomain !== refDomain) {
                  const res = channelDomainMapping.every(x => refDomain.indexOf(x) === -1);
                  if (res) return [channelId, refDomain];
                }
              } else {
                const res = channelDomainMapping.some(x => refDomain.indexOf(x) > -1);
                // Because unibet.co.uk contains t.co, added manual check below.
                if (res && refDomain.indexOf('unibet') === -1) return [channelId, refDomain];
              }
            }
          };
          // Check if a channel click-through was performed. Each channel has slightly different logic, especially referring domains and direct.
          // If no click-through is performed, no data is captured.
          const isChannelClickthrough = (channelParameter, referrer) => {
            // Conditions to set channel information:
            // 1. ch exists on the URL parameters
            // 2. ch does not exist but referring domain exists within any of the domains mapping
            // 3. ch does not exist, referring domain does not exist and it is start of visit -> Direct visit.
            // mark as we need to find a way without using tealium to get the first page view of the session
            const pageCount = localStorage.getItem('pageCount');
            let sessionHitNumber = parseInt(pageCount);
            if (channelParameter && channelParameter !== '') {
              return true;
            } else if (getTrackingCode() !== '') {
              return false;
            } else if (referrer && referrer !== '') {
              // Referrer needs to match any of the domain mappings
              if (identifyChannels(NATURAL_SEARCH, DOMAINS_NATURAL_SEARCH, referrer) || identifyChannels(NATURAL_SOCIAL, DOMAINS_NATURAL_SOCIAL, referrer) || identifyChannels(REFERRING_DOMAIN, DOMAINS_REFERRING, referrer)) return true;
            } else if (sessionHitNumber === 1 && referrer === '') return true;else return false;
          };
          const IS_CHANNEL_CTR = isChannelClickthrough(paramsObj.get('ch'), referrer);
          const helpIdentifyNaturalChannels = referrer => {
            // Natural search, Natural Social and Referring domains do not have ch and sub_ch parameters.
            const naturalSearchInfo = identifyChannels(NATURAL_SEARCH, DOMAINS_NATURAL_SEARCH, referrer);
            const natural_social_info = identifyChannels(NATURAL_SOCIAL, DOMAINS_NATURAL_SOCIAL, referrer);
            const referring_info = identifyChannels(REFERRING_DOMAIN, DOMAINS_REFERRING, referrer);
            if (naturalSearchInfo) {
              marketingChannelId = naturalSearchInfo[0];
              marketingSubChannelId = naturalSearchInfo[1];
            } else if (natural_social_info) {
              marketingChannelId = natural_social_info[0];
              marketingSubChannelId = natural_social_info[1];
            } else if (referring_info) {
              marketingChannelId = referring_info[0];
              marketingSubChannelId = referring_info[1];
            }
            return {
              marketingChannelId,
              marketingSubChannelId
            };
          };
          if (IS_CHANNEL_CTR) {
            if (paramsObj.has('ch')) {
              marketingChannelId = paramsObj.get('ch');
              if (paramsObj.get('ch') === AFFILIATE) {
                // Affiliate custom sub_channel
                const tmpBtag = paramsObj.get('btag');
                if (tmpBtag) marketingSubChannelId = tmpBtag.split('_')[0];
              } else if (paramsObj.get('ch') === SATELLITE_SITE) {
                // satellite sites sub_channel -> referring domain
                marketingSubChannelId = getDomainFromUrl(referrer);
              } else if (paramsObj.has('sub_ch')) marketingSubChannelId = paramsObj.get('sub_ch');else if (paramsObj.has('subch')) marketingSubChannelId = paramsObj.get('subch');
            } else {
              ({
                marketingChannelId,
                marketingSubChannelId
              } = helpIdentifyNaturalChannels(referrer));
            }
          } else if (OLD_TRACKING_CODE !== '') {
            if (/^44/i.test(OLD_TRACKING_CODE)) {
              marketingChannelId = 'paid_search';
            } else if (/^52/i.test(OLD_TRACKING_CODE)) {
              marketingChannelId = 'paid_social';
            } else if (/^49/i.test(OLD_TRACKING_CODE)) {
              marketingChannelId = 'display';
            } else if (/^popunder:/i.test(OLD_TRACKING_CODE)) {
              marketingChannelId = 'popunder';
            } else if (/^1/i.test(OLD_TRACKING_CODE)) {
              marketingChannelId = AFFILIATE;
              // Affiliate custom sub_channel
              var tmpBtag = paramsObj.get('btag');
              if (tmpBtag) marketingSubChannelId = tmpBtag.split('_')[0];
              var popunderIds = ['81764725', '81763824', '81763501', '81763091', '81750246', '81750186', '81750185', '81750179', '81749212', '81748885', '81748470', '81748371', '81746924', '81745741', '81744888', '81744811', '81744284', '81742790', '81742196', '6006407', '6005908', '6005292', '6005291', '6005264', '6005195', '320667814', '320667735', '320667448', '320667438', '320666043', '320665405', '127656443', '127656177', '127655244', '127654917', '127654816', '127654173', '81745104', '81747181', '81747374', '81747494', '81749955', '81763812', '320667825', '320667826', '320668861', '320669226', '320669583', '320669908'];
              var splitTrackingCode = OLD_TRACKING_CODE.split(':');
              if (popunderIds.indexOf(splitTrackingCode[1]) > -1) {
                marketingChannelId = 'popunder';
              }
            } else if (/^(email|46:|57:)/i.test(OLD_TRACKING_CODE)) {
              marketingChannelId = 'email';
            } else if (/^55/i.test(OLD_TRACKING_CODE)) {
              marketingChannelId = 'mobile_ads';
            } else if (/^50/i.test(OLD_TRACKING_CODE)) {
              marketingChannelId = 'satellite_site';
            } else if (/^PNF/i.test(OLD_TRACKING_CODE)) {
              marketingChannelId = 'push';
            } else {
              ({
                marketingChannelId,
                marketingSubChannelId
              } = helpIdentifyNaturalChannels(referrer));
            }
            marketingSubChannelId = OLD_TRACKING_CODE || '';
          }
          // All parameters are being captued from the URL
          marketingData.marketing_channel_id = marketingChannelId || '';
          marketingData.marketing_sub_channel_id = marketingSubChannelId || '';
          /* Set tracking code equal to subchannel if the channel is :
           *   Paid Search
           *   Paid Social
           *   Display
           *   Email
           *   Dedicated Mobile Ads
           *   Satellite sites
           */
          if (/^paid_(search|social)|display|email|mobile_ads|satellite_site$/.test(marketingChannelId)) {
            marketingData.campaign_tracking_code = marketingSubChannelId;
          }
          marketingData.marketing_kindred_placement_id = paramsObj.get('kpid') || '';
          marketingData.marketing_keyword = paramsObj.get('keyword') || '';
          marketingData.marketing_campaign_id = paramsObj.get('k_cid') || paramsObj.get('campaignId') || paramsObj.get('campaignid') || '';
          if (marketingData.marketing_channel_id === 'email' && (marketingData.marketing_campaign_id === '' || marketingData.marketing_campaign_id == 'notset')) {
            marketingData.marketing_campaign_id = paramsObj.get('templateid') || 'notset';
          }
          marketingData.marketing_btag = paramsObj.get('btag') || '';
          marketingData.marketing_nf_pid = paramsObj.get('pid') || '';
          marketingData.marketing_nf_bid = paramsObj.get('bid') || '';
          marketingData.marketing_network_id = paramsObj.get('affiliateid') || '';
          marketingData.marketing_ad_id = paramsObj.get('adid') || '';
          marketingData.marketing_product_info = paramsObj.get('productid') || '';
          marketingData.marketing_cct_tracking_id = paramsObj.get('trackingid') || '';
          if (paramsObj.get('trackingid2') !== null && (marketingData.marketing_cct_tracking_id === '' || marketingData.marketing_cct_tracking_id == 'notset')) {
            marketingData.marketing_cct_tracking_id = paramsObj.get('trackingid2') || '';
          }
          marketingData.marketing_cct_group_id = paramsObj.get('k_gid') || '';
          marketingData.marketing_recruiter_id = paramsObj.get('recruiterid') || '';
          marketingData.marketing_timestamp = Math.floor(Date.now() / 1000);
          marketingData.marketing_gamename = paramsObj.get('gamename') || '';
          marketingData.marketing_acquisition_offer_id = paramsObj.get('acquisitionofferid') || '';
          if (marketingData.marketing_channel_id !== '') {
            analyticsHelpers.setCookie('queryParameters', sanited_search, '');
          }
          if (paramsObj.get('page_referrer')) {
            window.snowplow('setReferrerUrl', paramsObj.get('page_referrer'));
          }
          return marketingData;
        };
        const getMarketingDataUpdated = () => {
          var _marketingData, _marketingData$sub_ch;
          /*
          the below function is the main function for marketingData
          it calls relevant functions below based on the query string type and/or channel (in the case of natural channels)
          */
          function structureMarketingData() {
            var _Object$keys;
            /*
            get query string from query parameters or queryString cookie 
            -the cookie is set on welcome pages and has two purposes:
            --the query string does not persist to the main sites, so we can still capture the query string
            --prevents us missing query string from private windows or ad-blockers as these can prevent GTM firing
            */
            let trackingCode = window.location.search;
            if (analyticsHelpers.getCookie('queryString')) {
              trackingCode = analyticsHelpers.getCookie('queryString');
              analyticsHelpers.deleteCookie('queryString');
            }
            let paramsObject = {};
            // Lowercase the entire query string for consistent parameter casing
            const lowerCaseTrackingCode = trackingCode.replace(/([^&?\/=]*)=/gi, x => x.toLowerCase());
            for (let [key, value] of new URLSearchParams(lowerCaseTrackingCode)) {
              paramsObject[key] = value;
            }
            //declare referrer
            let referrer = document.referrer;

            //popunder check and configure
            let isPopunder = false;
            if (referrer.indexOf('/pop/') > -1) {
              isPopunder = true;
              if (paramsObject.mktid) {
                paramsObject.mktid = paramsObject.mktid.replace('1:', 'popunder:');
              }
              if (paramsObject.cid) {
                paramsObject.cid = paramsObject.cid.replace('1:', 'popunder:');
              }
            }
            //paid channel check
            if (paramsObject && paramsObject !== '' && paramsObject !== null && ((_Object$keys = Object.keys(paramsObject)) === null || _Object$keys === void 0 ? void 0 : _Object$keys.length) > 0) {
              //bstan check
              if ('ch' in paramsObject) {
                marketingData = bstan(paramsObject);
              }
              //stan check
              else if (isPopunder || 'mktid' in paramsObject || 'cid' in paramsObject) {
                marketingData = stan(paramsObject);
              } else if ('utm_medium' in paramsObject) {
                marketingData.channel = paramsObject.utm_medium;
                const medium = paramsObject.utm_medium;
                const source = paramsObject.utm_source || 'NONE';
                const content = paramsObject.utm_content || 'NONE';
                const campaign = paramsObject.utm_campaign || 'NONE';
                const term = paramsObject.utm_term || 'NONE';
                marketingData.sub_channel = medium + ':' + source + ':' + content + ':' + campaign + ':' + term;
              }
            }
            //natural channel check
            else if (referrer && referrer !== '') {
              let naturalChannel = naturalChannelHandler(referrer);
              if (naturalChannel === 'search' || naturalChannel === 'social') {
                naturalChannel = 'natural_' + naturalChannel;
              } else if (naturalChannel !== 'banking' && naturalChannel !== 'internal') {
                naturalChannel = 'referring_domain';
              }
              marketingData.channel = naturalChannel;
              marketingData.sub_channel = referrer;
            }

            /*
            set Snowplow referrer for internal redirects, 
            this is for friendly pagepaths, they're shortened in SERPs but instantly redirect so the referrer needs to be set as query param
            */
            if (paramsObject.page_referrer && paramsObject.page_referrer !== '') {
              window.snowplow('setReferrerUrl', paramsObject.get('page_referrer'));
            }
            //returns marketing data to getMarketingDataUpdated function
            return marketingData;
          }

          //handling for bstan (beyond STAN) parameters, these should be in use across most channels
          function bstan(paramsObject) {
            let sub_ch = paramsObject.sub_ch;
            if (paramsObject.ch === 'affiliate' && paramsObject !== null && paramsObject !== void 0 && paramsObject.btag) {
              sub_ch = paramsObject === null || paramsObject === void 0 ? void 0 : paramsObject.btag.split('_')[0];
            }
            marketingData.channel = paramsObject.ch;
            marketingData.sub_channel = sub_ch;
            marketingData.kindred_placement_id = paramsObject.kpid || '';
            marketingData.ad_id = paramsObject.adid || '';
            marketingData.btag = paramsObject.btag || '';
            marketingData.campaign_id = paramsObject.k_cid || paramsObject.campaignid || '';
            marketingData.cct_group_id = paramsObject.k_gid || '';
            marketingData.cct_tracking_id = paramsObject.trackingid || '';
            marketingData.recruiter_id = paramsObject.recruiterid || '';
            marketingData.gamename = paramsObject.gamename || '';
            marketingData.acquisition_offer_id = paramsObject.acquisition_offer_id || '';
            marketingData.keyword = paramsObject.keyword || '';
            marketingData.nf_pid = paramsObject.pid || '';
            marketingData.nf_bid = paramsObject.bid || '';
            marketingData.network_id = paramsObject.affiliateid || '';
            marketingData.product_id = paramsObject.productid || '';
            //returns marketing data to the structureMarketingData function
            return marketingData;
          }

          //handling for stan (legacy) parameters, these are being phased out but we still receive some traffic using these
          function stan(paramsObject) {
            let mktid = paramsObject.mktid.split(':');
            let channelIds = {
              1: 'affiliate',
              44: 'paid_search',
              46: 'email',
              49: 'display',
              50: 'satellite_site',
              52: 'paid_social',
              55: 'mobile_ads',
              57: 'email',
              popunder: 'popunder',
              email: 'email',
              PNF: 'push'
            };
            if (channelIds[mktid[0]]) {
              marketingData.channel = channelIds[mktid[0]];
            }
            let popunderIds = ['81764725', '81763824', '81763501', '81763091', '81750246', '81750186', '81750185', '81750179', '81749212', '81748885', '81748470', '81748371', '81746924', '81745741', '81744888', '81744811', '81744284', '81742790', '81742196', '6006407', '6005908', '6005292', '6005291', '6005264', '6005195', '320667814', '320667735', '320667448', '320667438', '320666043', '320665405', '127656443', '127656177', '127655244', '127654917', '127654816', '127654173', '81745104', '81747181', '81747374', '81747494', '81749955', '81763812', '320667825', '320667826', '320668861', '320669226', '320669583', '320669908'];
            if (popunderIds.indexOf(mktid[1]) > -1) {
              marketingData.channel = 'popunder';
              marketingData.sub_channel = getTrackingCode().split(':')[1];
              marketingData.kindred_placement_id = paramsObject.kpid || '';
              marketingData.ad_id = paramsObject.adid || '';
              marketingData.btag = paramsObject.btag || '';
              marketingData.campaign_id = paramsObject.k_cid || paramsObject.campaignid || '';
              marketingData.cct_group_id = paramsObject.k_gid || '';
              marketingData.cct_tracking_id = paramsObject.trackingid || '';
              marketingData.recruiter_id = paramsObject.recruiterid || '';
              marketingData.gamename = paramsObject.gamename || '';
              marketingData.acquisition_offer_id = paramsObject.acquisition_offer_id || '';
              marketingData.keyword = paramsObject.keyword || '';
              marketingData.nf_pid = paramsObject.pid || '';
              marketingData.nf_bid = paramsObject.bid || '';
              marketingData.network_id = paramsObject.affiliateid || '';
              marketingData.product_id = paramsObject.productid || '';
            }
            //returns marketing data to the structureMarketingData function
            return marketingData;
          }

          /*
          natural channel identification; these channels don't typically have query strings so are identified from the referrer
          */
          function naturalChannelHandler(referrer) {
            let naturalChannels = {
              internal: ['.unibet.', '.unibetcasino.', '.unibetgames.', '.unibetsports.', '.bingo.', '.vladcazino.', '.highroller.', '.highrolling.', '.storspelare.', '.storspiller.', '.igame.', '.casinohuone.', '.kolikkopelit.', '.mariacasino.', 'paypal.com', 'merchant.itsme', '.32red.', '.32rosu.', '.ottokasino', '.ottocasino.'],
              banking: ['diensten.snsbank.nl', '.abnamro.nl', 'diensten.asnbank.nl', 'idin.bunq.com', 'ideal.ing.nl', 'idp.rabobank.nl', 'diensten.regiobank.nl', 'diensten.snsbank.nl', 'unibet.criipto.id', 'unibet.mitid.dk'],
              search: ['www.google.', 'bing.', 'search.yahoo.', 'search.seznam.', '.yandex.', '.ask.'],
              social: ['facebook.com', 't.co', 'pinterest.', 'linked.com', 'plus.google', 'instagram.com', 'hootsuite.com']
            };
            for (const [channel, patterns] of Object.entries(naturalChannels)) {
              if (patterns.some(pattern => referrer.includes(pattern))) {
                //returns the channel to the structureMarketingData function
                return channel;
              }
            }
            return null;
          }
          //calls the main marketingData handling function
          structureMarketingData();
          //return null for internal sites
          if (marketingData.channel === 'internal' || marketingData.channel === 'banking') {
            marketingData = {};
            return null;
          }
          //prevent event failure due to referrers with query strings
          if (((_marketingData = marketingData) === null || _marketingData === void 0 ? void 0 : (_marketingData$sub_ch = _marketingData.sub_channel) === null || _marketingData$sub_ch === void 0 ? void 0 : _marketingData$sub_ch.length) > 250) {
            marketingData.sub_channel = marketingData.sub_channel.substring(0, 250);
          }
          //prevent event failure due to missing subChan
          if (marketingData.channel === 'popunder' && !marketingData.sub_channel) {
            marketingData.sub_channel = marketingData.btag.split('_')[0];
          }
          //returns marketing data to whichever function called getMarketingDataUpdated
          return marketingData;
        };
        return {
          getMarketingData,
          getMarketingDataUpdated
        };
      };

      var fire_adform = function (pageName, pm, item) {
        window._adftrack = Array.isArray(window._adftrack) ? window._adftrack : window._adftrack ? [window._adftrack] : [];
        window._adftrack.push({
          HttpHost: 'track.adform.net',
          pm: pm,
          divider: encodeURIComponent('|'),
          pagename: encodeURIComponent(pageName),
          order: item
        });
        (function () {
          var s = document.createElement('script');
          s.type = 'text/javascript';
          s.async = true;
          s.src = 'https://s2.adform.net/banners/scripts/st/trackpoint-async.js';
          var x = document.getElementsByTagName('script')[0];
          x.parentNode.insertBefore(s, x);
        })();
      };
      function adformFire(tagMap, type, data) {
        const {
          brand,
          market
        } = useDataLayer();
        let capitalisedBrand = brand.charAt(0).toUpperCase() + brand.slice(1);
        let adfMarket = capitalisedBrand + " " + market;
        let adfLabelMap = {
          "firstDeposit": "First Deposit Intent",
          "furtherDeposit": "Further Deposit Intent",
          "pageView": "Site Tracking_Page Views",
          "registrationStart": "Registration Start",
          "registrationSuccessful": "Registration Success",
          "loginSuccess": "Login Success"
        };
        let adfPageName = 'Adform_' + adfMarket + "_CS " + adfLabelMap[type];
        var adformPayload = function (type, data) {
          let depositAmount = (data === null || data === void 0 ? void 0 : data.amount) || 0;
          let transactionId = (data === null || data === void 0 ? void 0 : data.paymentTransactionId) || "";
          let userId = getCustomerId(data);
          let depositNumber = (data === null || data === void 0 ? void 0 : data.noOfDeposits) || 0;
          let timestamp = (data === null || data === void 0 ? void 0 : data.timestamp) || Date.now() || "";
          const {
            currency
          } = useDataLayer();
          var itm = {};
          if (depositAmount) {
            itm['sl'] = depositAmount;
            itm['sales'] = depositAmount;
          }
          if (transactionId) {
            itm['id'] = transactionId;
            itm['orderid'] = transactionId;
          }
          if (userId) {
            itm['sv1'] = userId;
          }
          if (depositNumber) {
            itm['sv2'] = depositNumber;
          }
          itm['sv3'] = timestamp;
          itm['sv4'] = getTrackingCode();
          itm['sv5'] = currency;

          //itm['sv7'] = sessionId
          /*
          if (b.event_name === 'GameLaunch') {
              var gameInfo = b.adb_game_info.split(', ');
              b.adf_gameId = gameInfo[0].split(': ')[1];
              b.adf_gameName = gameInfo[1].split(': ')[1];
              b.adf_gameType = b.adb_money_mode;
          }
           itm['sv8']= gameId
          itm['sv9'] = gameName ;
          itm['sv10'] = gameType ;
          */

          itm['sv11'] = data === null || data === void 0 ? void 0 : data.purchase_id;
          itm['sv12'] = data === null || data === void 0 ? void 0 : data.total_revenue;
          /*
          itm['sv14'] = hit_event_id ;
          itm['sv21'] = document.referrer
          */

          return itm;
        };
        if (type !== 'pageView') {
          var item = adformPayload(type, data);
          fire_adform(adfPageName, tagMap.id, item);
        } else {
          fire_adform(adfPageName, tagMap.id, {});
        }
      }

      function bingConfig(id) {
        if (typeof window === 'object' && typeof document === 'object') {
          window.uetq = window.uetq || [];
          (function (w, d, t, r, u) {
            var f, n, i;
            w[u] = w[u] || [], f = function () {
              var o = {
                ti: id,
                enableAutoSpaTracking: true
              };
              o.q = w[u], w[u] = new UET(o), w[u].push("pageLoad");
            }, n = d.createElement(t), n.src = r, n.async = 1, n.onload = n.onreadystatechange = function () {
              var s = this.readyState;
              s && s !== "loaded" && s !== "complete" || (f(), n.onload = n.onreadystatechange = null);
            }, i = d.getElementsByTagName(t)[0], i.parentNode.insertBefore(n, i);
          })(window, document, "script", "//bat.bing.com/bat.js", "uetq");
        }
      }
      function bingFire(tagMap, type, data) {
        if (!window.uetq) {
          bingConfig(tagMap.id);
        }
        // type takes values loginSuccess, firstDeposit, registrationSuccessful

        // Event category -> labels
        let eventMapping = {
          'loginSuccess': {
            'eventName': 'Login',
            'eventCategory': 'Login',
            'eventLabel': 'Returning'
          },
          'firstDeposit': {
            'eventName': 'first-deposit',
            'eventCategory': 'FTD',
            'eventLabel': 'Deposit'
          },
          'registrationSuccessful': {
            'eventName': 'Registration',
            'eventCategory': 'Registration',
            'eventLabel': 'SignUp'
          },
          'furtherDeposit': {
            'eventName': 'further-deposit',
            'eventCateogry': 'FurtherDeposit',
            'eventLabel': 'Deposit'
          }
        };
        if (type in eventMapping) {
          window.uetq.push('event', eventMapping[type]['eventName'], {
            'event_category': eventMapping[type]['eventCategory'],
            'event_label': eventMapping[type]['eventLabel'],
            'event_value': '0'
          });
        }
      }

      /*let eventLabel = {
          firstDeposit:'first-deposit',
          furtherDeposit:'further-deposit',
          registrationSuccessful:'Registration'
      }
      let event_category = eventLabel[type];
      let event_label = "";
      let event_value = "";
      var payload = {
          'event_category': event_category, 
          'event_label': event_label, 
          'event_value': event_value
      }

      window.uetq = window.uetq || [];
      window.uetq.push('event', 'Click', payload);*/

      function googleConfig(id) {
        var googleTag = document.createElement('script');
        googleTag.nonce = getScriptNonce();
        googleTag.src = 'https://www.googletagmanager.com/gtag/js?id=' + id;
        googleTag.async = true;
        document.head.appendChild(googleTag);
        window.dataLayer = window.dataLayer || [];
        window.gtag = function () {
          dataLayer.push(arguments);
        };
        gtag('js', new Date());
        try {
          if (!consentModeCheck()) {
            googleConsentModeInit();
          }
        } catch (error) {
          logToSplunk$1(error, type, data, 'googleConfigCheck');
        }
        gtag('config', id);
      }
      function googlePayload(eventName, data) {
        const {
          getMarketingDataUpdated
        } = marketingData();
        let mkData = getMarketingDataUpdated();
        try {
          if ((mkData === null || mkData === void 0 ? void 0 : mkData.marketing_channel_id) === "") {
            var params;
            var paramsArray = [];
            var splitParams;
            var arr;
            if (analyticsHelpers.getCookie('queryParameters') === "") {
              return;
            }
            params = decodeURIComponent(analyticsHelpers.getCookie('queryParameters'));
            arr = params.split('&');
            for (var i = 0; i < arr.length; i++) {
              splitParams = arr[i].split('=')[1];
              paramsArray.push(splitParams);
            }
            if (mkData) {
              mkData.marketing_channel_id = paramsArray[0] || "";
              mkData.marketing_sub_channel_id = paramsArray[1] || "";
              mkData.marketing_kindred_placement_id = paramsArray[2] || "";
            }
          }
        } catch (error) {
          logToSplunk$1(error, eventName, data, 'googlePayload');
        }
        let eventLabel = {
          'pageView': 'page view',
          'firstDeposit': 'First deposit intent',
          'furtherDeposit': 'Further deposit intent',
          'registrationStart': 'Registration start',
          'registrationSuccessful': 'Registration complete',
          'loginSuccess': 'Login successful',
          'addBet': 'Add bet',
          'placeBet': 'Place bet',
          'genericBannerInteraction': 'Banner click'
        };
        //allocate variables from evt
        const {
          clientId,
          currency
        } = useDataLayer();
        let userId = getCustomerId(data);
        let timestamp = (data === null || data === void 0 ? void 0 : data.timestamp) || Date.now() || "";
        let floodlight_u3 = eventLabel[eventName];
        let visitorId = "visitorId";
        let sessionId = "sessionId";
        let deviceBrowser = clientId.split("_")[1] + ":" + analyticsHelpers.getBrowserInfo();
        let currencyHolder = currency;
        let depositNumber = (data === null || data === void 0 ? void 0 : data.noOfDeposits) || 0;
        let depositAmount = (data === null || data === void 0 ? void 0 : data.amount) || 0;
        let transactionId = (data === null || data === void 0 ? void 0 : data.paymentTransactionId) || "";
        let url = window.location.href;
        let marketingChannelIdStored = (mkData === null || mkData === void 0 ? void 0 : mkData.marketing_channel_id) || "";
        let marketingSubChannelIdStored = (mkData === null || mkData === void 0 ? void 0 : mkData.marketing_sub_channel_id) || "";
        let marketingKpidStored = (mkData === null || mkData === void 0 ? void 0 : mkData.marketing_kindred_placement_id) || "";
        let floodlightType = 'conversion';
        let random = timestamp + Math.random();
        let ord = Number(random);
        let betRevenue = "";
        let betId = "";
        let bannerLocation = "";
        let bannerDestination = "";
        let pageCount = 0;
        let product = "";
        let sport = "";
        const pathname = window.location.pathname.toLowerCase();
        if (/\/betting\/odds/.test(pathname)) {
          product = 'kspSportsbook';
        } else if (/\/racing/.test(pathname)) {
          product = 'racing';
        } else if (/\/live-?casino/.test(pathname)) {
          product = 'live casino';
        } else if (/\/casino/.test(pathname)) {
          product = 'casino';
        } else if (/\/bingo/.test(pathname)) {
          product = 'bingo';
        } else if (/\/poker/.test(pathname)) {
          product = 'poker';
        } else if (/\/sport/.test(pathname) || /\/sportsbook/.test(pathname)) {
          product = 'sportsbook';
        }
        if (eventName === 'addBet' || eventName === 'placeBet') {
          var _data$ecommerce, _data$ecommerce$add, _data$ecommerce2, _data$ecommerce2$purc, _data$ecommerce3, _data$ecommerce3$deta, _kambiProducts$, _data$detail, _data$detail$contest, _data$detail$contest$;
          const kambiProducts = (data === null || data === void 0 ? void 0 : (_data$ecommerce = data.ecommerce) === null || _data$ecommerce === void 0 ? void 0 : (_data$ecommerce$add = _data$ecommerce.add) === null || _data$ecommerce$add === void 0 ? void 0 : _data$ecommerce$add.products) || (data === null || data === void 0 ? void 0 : (_data$ecommerce2 = data.ecommerce) === null || _data$ecommerce2 === void 0 ? void 0 : (_data$ecommerce2$purc = _data$ecommerce2.purchase) === null || _data$ecommerce2$purc === void 0 ? void 0 : _data$ecommerce2$purc.products) || (data === null || data === void 0 ? void 0 : (_data$ecommerce3 = data.ecommerce) === null || _data$ecommerce3 === void 0 ? void 0 : (_data$ecommerce3$deta = _data$ecommerce3.detail) === null || _data$ecommerce3$deta === void 0 ? void 0 : _data$ecommerce3$deta.products) || [];
          if (kambiProducts.length > 0 && (_kambiProducts$ = kambiProducts[0]) !== null && _kambiProducts$ !== void 0 && _kambiProducts$.category) {
            sport = kambiProducts[0].category.split('/')[0].trim().toLowerCase().replace(/\s+/g, '_');
          }
          if (!sport && data !== null && data !== void 0 && (_data$detail = data.detail) !== null && _data$detail !== void 0 && (_data$detail$contest = _data$detail.contest) !== null && _data$detail$contest !== void 0 && (_data$detail$contest$ = _data$detail$contest[0]) !== null && _data$detail$contest$ !== void 0 && _data$detail$contest$.category) {
            sport = data.detail.contest[0].category.split(':')[0].trim().toLowerCase().replace(/\s+/g, '_');
          }
        }
        if (eventName === 'genericBannerInteraction') {
          bannerLocation = data.header;
          bannerDestination = data.value;
        }
        if (eventName === "placeBet") {
          if (data !== null && data !== void 0 && data.ecommerce) {
            betRevenue = data.ecommerce.purchase.actionField.revenue;
            betId = data.ecommerce.purchase.actionField.id;
          } else {
            betRevenue = data.detail.coupon.couponStake || 0;
            betId = data.detail.coupon.couponId || "";
          }
        }
        if (transactionId) {
          floodlightType = 'purchase';
          ord = transactionId;
        }
        if (floodlight_u3 === "page view") {
          pageCount = sessionStorage.getItem('pageCount');
        }

        /* let str = Math.random().toString();
         let random = str.replace(/0\./,"")
         let num = timestamp+"."+random
         let betterNum = Number(num)
         */
        let payload = {
          'allow_custom_scripts': true,
          'u1': userId,
          'u2': timestamp,
          'u3': floodlight_u3,
          'u4': visitorId,
          'u5': sessionId,
          'u6': marketingChannelIdStored,
          'u7': document.referrer,
          'u8': deviceBrowser,
          'u9': currencyHolder,
          'u10': depositNumber,
          'u11': depositAmount,
          'u12': transactionId,
          'u13': betId,
          'u14': '',
          //bet counter
          'u15': '',
          //bet amount
          'u16': betRevenue,
          'u17': url,
          'u18': marketingSubChannelIdStored,
          'u19': marketingKpidStored,
          'u20': bannerLocation,
          'u21': bannerDestination,
          'u22': pageCount,
          'u25': product,
          'u26': sport,
          'transaction_id': ord,
          'value': depositAmount
        };
        const deleteEmpty = ["", 0, null, undefined];
        //startTransition(() => {
        for (var i in payload) {
          if (deleteEmpty.includes(payload[i])) {
            delete payload[i];
          }
        }
        //})
        return {
          payload,
          floodlightType
        };
      }
      function googleFire(tagMap, type, data, googleType) {
        try {
          var _window;
          if (typeof ((_window = window) === null || _window === void 0 ? void 0 : _window.gtag) !== 'function') {
            googleConfig(tagMap.id);
          }
        } catch (error) {
          logToSplunk$1(error, type, data, 'googleFire');
        }
        let {
          payload,
          floodlightType
        } = googlePayload(type, data);
        payload['send_to'] = tagMap.id;
        if (googleType === "cm360" || googleType === 'adwords' || googleType === 'adwordsYoutube') {
          if (type === 'genericBannerInteraction') {
            return;
          }
          let registrationFlag = analyticsHelpers.storageManagement._getStorage("sessionStorage", "registrationStepsAnalytics") || {};
          let nl_url = /www\-(qa1|si1)\.unibet\.nl/g;
          if (nl_url.test(window.location.hostname)) {
            if (!Object.keys(registrationFlag).includes("welcome offer screen") && type === 'registrationSuccessful') {
              return;
            }
          }
          payload['send_to'] = tagMap.id + "/" + tagMap[type];
        }
        if (googleType === 'ga4' && payload.u3 === "page view") {
          if (payload.u22 > 1) {
            const timestamp = Date.now();
            const previousTimestamp = analyticsHelpers.storageManagement._getStorage("sessionStorage", "previous_timestamp");
            const previousPath = analyticsHelpers.storageManagement._getStorage("sessionStorage", "previous_path");
            if (previousTimestamp) {
              payload['u23'] = new Date(timestamp - previousTimestamp).toISOString().slice(11, 19);
              payload['u24'] = previousPath;
            }
            analyticsHelpers.storageManagement._setStorage("sessionStorage", "previous_timestamp", timestamp);
            analyticsHelpers.storageManagement._setStorage("sessionStorage", "previous_path", window.location.pathname);
          }
        }
        if (!gtag) {
          window.dataLayer = window.dataLayer || [];
          gtag = function () {
            dataLayer.push(arguments);
          };
        }
        gtag('event', floodlightType, payload);
      }
      function googleConsentModeInit() {
        window.dataLayer = window.dataLayer || [];
        function gtag() {
          dataLayer.push(arguments);
        }
        gtag('consent', 'default', {
          'ad_storage': 'denied',
          'analytics_storage': 'denied',
          'ad_user_data': 'denied',
          'ad_personalization': 'denied'
        });
        if (getMarketingConsent()) {
          gtag('consent', 'update', {
            'ad_storage': 'granted',
            'analytics_storage': 'granted',
            'ad_user_data': 'granted',
            'ad_personalization': 'granted'
          });
        }
      }
      function consentModeCheck() {
        let consentMode = false;
        for (let i in (_window3 = window) === null || _window3 === void 0 ? void 0 : _window3.dataLayer) {
          var _window3;
          if (window.dataLayer[i][0] === 'consent') {
            consentMode = true;
          }
        }
        return consentMode;
      }

      function metaConfig(id, data) {
        let userId = getCustomerId(data);
        !function (f, b, e, v, n, t, s) {
          if (f.fbq) return;
          n = f.fbq = function () {
            n.callMethod ? n.callMethod.apply(n, arguments) : n.queue.push(arguments);
          };
          if (!f._fbq) f._fbq = n;
          n.push = n;
          n.loaded = !0;
          n.version = '2.0';
          n.queue = [];
          t = b.createElement(e);
          t.async = !0;
          t.src = v;
          s = b.getElementsByTagName(e)[0];
          s.parentNode.insertBefore(t, s);
        }(window, document, 'script', 'https://connect.facebook.net/en_US/fbevents.js');
        if (/www(-(qa|si|pt)1)?\.unibet\.com\.au/.test(window.location.hostname) && userId !== 0) {
          fbq('init', id, {
            'external_id': userId
          });
        } else {
          fbq('init', id);
        }
      }
      function metaFire(id, type, data) {
        try {
          if (!fbq || typeof fbq !== 'function') {
            metaConfig(id, data);
          }
        } catch (error) {
          logToSplunk(error, type, data, 'metaConfigCheck');
        }
        let depositNumber = (data === null || data === void 0 ? void 0 : data.noOfDeposits) || 0;
        let depositAmount = (data === null || data === void 0 ? void 0 : data.amount) || 0;
        let is_first_deposit = 0;
        let eventId = {};
        if (/deposit/i.test(type)) {
          eventId = {
            eventID: data === null || data === void 0 ? void 0 : data.paymentTransactionId
          };
        }
        if (type === 'registrationSuccessful') {
          eventId = {
            eventID: getCustomerId(data)
          };
        }
        if (type === 'firstDeposit') {
          is_first_deposit = 1;
        }
        let eventLabel = {
          'pageView': 'PageView',
          'firstDeposit': 'Purchase',
          'furtherDeposit': 'Subscribe',
          'regStart': 'RegistrationStart',
          'registrationSuccessful': 'CompleteRegistration',
          'loginSuccess': 'Login Success'
        };
        const {
          currency
        } = useDataLayer();
        let payload = {
          'currency': currency,
          'deposit_number': depositNumber,
          'value': depositAmount,
          'is_first_deposit': is_first_deposit
        };
        const deleteEmpty = ["", 0, null, undefined];
        for (var i in payload) {
          if (deleteEmpty.includes(payload[i])) {
            delete payload[i];
          }
        }
        fbq('track', eventLabel[type], payload, eventId);
      }

      function snapchatConfig(id) {
        if (typeof snaptr !== 'function') {
          (function (e, t, n) {
            if (e.snaptr) return;
            var a = e.snaptr = function () {
              a.handleRequest ? a.handleRequest.apply(a, arguments) : a.queue.push(arguments);
            };
            a.queue = [];
            var s = 'script';
            var r = t.createElement(s);
            r.async = !0;
            r.src = n;
            var u = t.getElementsByTagName(s)[0];
            u.parentNode.insertBefore(r, u);
          })(window, document, 'https://sc-static.net/scevent.min.js');
          snaptr('init', id);
        }
      }
      function snapchatFire(tagMap, type, data) {
        if (typeof snaptr !== 'function') {
          snapchatConfig(tagMap.id);
        }
        let depositNumber = (data === null || data === void 0 ? void 0 : data.noOfDeposits) || 0;
        let transactionId = (data === null || data === void 0 ? void 0 : data.paymentTransactionId) || "";
        let eventId = 0;
        if (type === 'registrationSuccessful') {
          eventId = getCustomerId(data);
        } else if (/deposit/i.test(type)) {
          eventId = transactionId;
        }
        let eventLabel = {
          'pageView': 'PageView',
          'firstDeposit': 'Purchase',
          'furtherDeposit': 'Add billing',
          'registrationSuccessful': 'Sign up'
        };
        const {
          currency
        } = useDataLayer();
        let payload = {
          'currency': currency,
          'deposit_number': depositNumber,
          'transaction_id': transactionId,
          'event_id': eventId
        };
        const deleteEmpty = ["", 0, null, undefined];
        for (var i in payload) {
          if (deleteEmpty.includes(payload[i])) {
            delete payload[i];
          }
        }
        snaptr('track', eventLabel[type], payload);
      }

      function redditConfig(id) {
        if (typeof rdt !== 'function') {
          !function (w, d) {
            if (!w.rdt) {
              var p = w.rdt = function () {
                p.sendEvent ? p.sendEvent.apply(p, arguments) : p.callQueue.push(arguments);
              };
              p.callQueue = [];
              var t = d.createElement("script");
              t.src = "https://www.redditstatic.com/ads/pixel.js", t.async = !0;
              var s = d.getElementsByTagName("script")[0];
              s.parentNode.insertBefore(t, s);
            }
          }(window, document);
          rdt('init', id);
        }
      }
      function redditFire(tagMap, type, data) {
        if (typeof rdt !== 'function') {
          redditConfig(tagMap.id);
        }
        let eventLabel = {
          'pageView': 'PageVisit',
          'firstDeposit': 'Purchase',
          'furtherDeposit': 'Lead',
          'registrationSuccessful': 'SignUp'
        };
        rdt('track', eventLabel[type]);
      }

      /*
      unibet/b.reddit_event_name = "";

      if (a=="view") {
          b.reddit_event_name = "pageLoaded"
      }else if(b.event_name==="depositRequested"){
          var depositNumber = b.deposit_number || 1;
          if(typeof b.noOfDeposits!=="undefined" && b.noOfDeposits!==null && /[0-9]{1,}/i.test(b.noOfDeposits) && depositNumber == 1 ){
              depositNumber = parseInt(b.noOfDeposits);
          }
          b.reddit_event_name = "furtherDeposit";
          if(depositNumber===1) {
              b.reddit_event_name = "firstDeposit";
          }
          
      }else if(/registrationSuccessful/i.test(b.event_name)){
          b.reddit_event_name = "registrationSuccess";
      } else {
          // Block tag execution
          return false;
      }
      */

      function pixieInit() {
        if (typeof pixie !== 'function') {
          !function (e, i) {
            if (!e.pixie) {
              var n = e.pixie = function (e, i, a) {
                n.actionQueue.push({
                  action: e,
                  actionValue: i,
                  params: a
                });
              };
              n.actionQueue = [];
              var a = i.createElement("script");
              a.async = !0, a.src = "//acdn.adnxs.com/dmp/up/pixie.js";
              var t = i.getElementsByTagName("head")[0];
              t.insertBefore(a, t.firstChild);
            }
          }(window, document);
        }
      }
      function xandrConfig(id) {
        if (typeof pixie !== 'function') {
          pixieInit();
        }
        pixie('init', id);

        // pixie('event', 'PageView')
        /*
        window.pixie.config = {
         logging: true
         }
         */
      }
      function xandrFire(tagMap, type, data) {
        let item_type = (data === null || data === void 0 ? void 0 : data.site_section) || "";
        let item_id = (data === null || data === void 0 ? void 0 : data.customer_id) || "";
        (data === null || data === void 0 ? void 0 : data.customer_id) || "";
        let item_name = "";
        let value = (data === null || data === void 0 ? void 0 : data.deposit_amount) || "";
        const {
          currency
        } = useDataLayer();
        let xandrObject = {
          "&consent": "1",
          "&e=": type,
          "&va=": value,
          "&ii=": item_id,
          "&in=": item_name,
          "&itp=": item_type,
          "&c=": currency
        };
        const deleteEmpty = ["", 0, null, undefined];
        for (var i in xandrObject) {
          if (deleteEmpty.includes(xandrObject[i])) {
            delete xandrObject[i];
          }
        }
        let xandrPayload = Object.entries(xandrObject).map(_ref => {
          let [key, value] = _ref;
          return key + value;
        }).join("");
        if (tagMap.method === "new") {
          xandrSend(xandrPayload, tagMap, tagMap.id);
        } else if (tagMap.method === "old") {
          if (type === 'pageView') {
            var _tagMap$pageview;
            appendXandrImg(tagMap.id, "PageView", xandrPayload);
            if ((tagMap === null || tagMap === void 0 ? void 0 : (_tagMap$pageview = tagMap.pageview) === null || _tagMap$pageview === void 0 ? void 0 : _tagMap$pageview.segment_id) !== '') {
              var _tagMap$pageview2;
              appendXandrSegmentImg(tagMap === null || tagMap === void 0 ? void 0 : (_tagMap$pageview2 = tagMap.pageview) === null || _tagMap$pageview2 === void 0 ? void 0 : _tagMap$pageview2.segment_id, xandrPayload);
            }
            if (/^\/registration\/?$/i.test(location.pathname)) {
              var _tagMap$registrationS, _tagMap$registrationS2;
              appendXandrConversionImg(tagMap === null || tagMap === void 0 ? void 0 : (_tagMap$registrationS = tagMap.registrationStart) === null || _tagMap$registrationS === void 0 ? void 0 : _tagMap$registrationS.pixel_id, xandrPayload);
              if ((tagMap === null || tagMap === void 0 ? void 0 : (_tagMap$registrationS2 = tagMap.registrationStart) === null || _tagMap$registrationS2 === void 0 ? void 0 : _tagMap$registrationS2.segment_id) !== '') {
                var _tagMap$registrationS3;
                appendXandrSegmentImg(tagMap === null || tagMap === void 0 ? void 0 : (_tagMap$registrationS3 = tagMap.registrationStart) === null || _tagMap$registrationS3 === void 0 ? void 0 : _tagMap$registrationS3.segment_id, xandrPayload);
              }
            } else if (/^(\/(home)?)$/i.test(location.pathname)) {
              var _tagMap$homepage, _tagMap$homepage2;
              appendXandrConversionImg(tagMap === null || tagMap === void 0 ? void 0 : (_tagMap$homepage = tagMap.homepage) === null || _tagMap$homepage === void 0 ? void 0 : _tagMap$homepage.pixel_id, xandrPayload);
              if ((tagMap === null || tagMap === void 0 ? void 0 : (_tagMap$homepage2 = tagMap.homepage) === null || _tagMap$homepage2 === void 0 ? void 0 : _tagMap$homepage2.segment_id) !== '') {
                var _tagMap$homepage3;
                appendXandrSegmentImg(tagMap === null || tagMap === void 0 ? void 0 : (_tagMap$homepage3 = tagMap.homepage) === null || _tagMap$homepage3 === void 0 ? void 0 : _tagMap$homepage3.segment_id, xandrPayload);
              }
            } else if (/^\/promotions\/casino-promotions/i.test(location.pathname)) {
              var _tagMap$casinopromoti, _tagMap$casinopromoti2;
              appendXandrConversionImg(tagMap === null || tagMap === void 0 ? void 0 : (_tagMap$casinopromoti = tagMap.casinopromotionpage) === null || _tagMap$casinopromoti === void 0 ? void 0 : _tagMap$casinopromoti.pixel_id, xandrPayload);
              if ((tagMap === null || tagMap === void 0 ? void 0 : (_tagMap$casinopromoti2 = tagMap.casinopromotionpage) === null || _tagMap$casinopromoti2 === void 0 ? void 0 : _tagMap$casinopromoti2.segment_id) !== '') {
                var _tagMap$casinopromoti3;
                appendXandrSegmentImg(tagMap === null || tagMap === void 0 ? void 0 : (_tagMap$casinopromoti3 = tagMap.casinopromotionpage) === null || _tagMap$casinopromoti3 === void 0 ? void 0 : _tagMap$casinopromoti3.segment_id, xandrPayload);
              }
            } else if (/^\/promotions\/sportsbook-promotions/i.test(location.pathname)) {
              var _tagMap$sportsbookpro, _tagMap$sportsbookpro2;
              appendXandrConversionImg(tagMap === null || tagMap === void 0 ? void 0 : (_tagMap$sportsbookpro = tagMap.sportsbookpromotionpage) === null || _tagMap$sportsbookpro === void 0 ? void 0 : _tagMap$sportsbookpro.pixel_id, xandrPayload);
              if ((tagMap === null || tagMap === void 0 ? void 0 : (_tagMap$sportsbookpro2 = tagMap.sportsbookpromotionpage) === null || _tagMap$sportsbookpro2 === void 0 ? void 0 : _tagMap$sportsbookpro2.segment_id) !== '') {
                var _tagMap$sportsbookpro3;
                appendXandrSegmentImg(tagMap === null || tagMap === void 0 ? void 0 : (_tagMap$sportsbookpro3 = tagMap.sportsbookpromotionpage) === null || _tagMap$sportsbookpro3 === void 0 ? void 0 : _tagMap$sportsbookpro3.segment_id, xandrPayload);
              }
            } else if (/^\/betting\/?/i.test(location.pathname)) {
              var _tagMap$sportsbookpag, _tagMap$sportsbookpag2;
              appendXandrConversionImg(tagMap === null || tagMap === void 0 ? void 0 : (_tagMap$sportsbookpag = tagMap.sportsbookpages) === null || _tagMap$sportsbookpag === void 0 ? void 0 : _tagMap$sportsbookpag.pixel_id, xandrPayload);
              if ((tagMap === null || tagMap === void 0 ? void 0 : (_tagMap$sportsbookpag2 = tagMap.sportsbookpages) === null || _tagMap$sportsbookpag2 === void 0 ? void 0 : _tagMap$sportsbookpag2.segment_id) !== '') {
                var _tagMap$sportsbookpag3;
                appendXandrSegmentImg(tagMap === null || tagMap === void 0 ? void 0 : (_tagMap$sportsbookpag3 = tagMap.sportsbookpages) === null || _tagMap$sportsbookpag3 === void 0 ? void 0 : _tagMap$sportsbookpag3.segment_id, xandrPayload);
              }
            } else if (/^\/racing\/?/i.test(location.pathname)) {
              var _tagMap$racingpages, _tagMap$racingpages2;
              appendXandrConversionImg(tagMap === null || tagMap === void 0 ? void 0 : (_tagMap$racingpages = tagMap.racingpages) === null || _tagMap$racingpages === void 0 ? void 0 : _tagMap$racingpages.pixel_id, xandrPayload);
              if ((tagMap === null || tagMap === void 0 ? void 0 : (_tagMap$racingpages2 = tagMap.racingpages) === null || _tagMap$racingpages2 === void 0 ? void 0 : _tagMap$racingpages2.segment_id) !== '') {
                var _tagMap$racingpages3;
                appendXandrSegmentImg(tagMap === null || tagMap === void 0 ? void 0 : (_tagMap$racingpages3 = tagMap.racingpages) === null || _tagMap$racingpages3 === void 0 ? void 0 : _tagMap$racingpages3.segment_id, xandrPayload);
              }
            } else if (/^\/(casino|play)\/?/i.test(location.pathname)) {
              var _tagMap$casinopages, _tagMap$casinopages2;
              appendXandrConversionImg(tagMap === null || tagMap === void 0 ? void 0 : (_tagMap$casinopages = tagMap.casinopages) === null || _tagMap$casinopages === void 0 ? void 0 : _tagMap$casinopages.pixel_id, xandrPayload);
              if ((tagMap === null || tagMap === void 0 ? void 0 : (_tagMap$casinopages2 = tagMap.casinopages) === null || _tagMap$casinopages2 === void 0 ? void 0 : _tagMap$casinopages2.segment_id) !== '') {
                var _tagMap$casinopages3;
                appendXandrSegmentImg(tagMap === null || tagMap === void 0 ? void 0 : (_tagMap$casinopages3 = tagMap.casinopages) === null || _tagMap$casinopages3 === void 0 ? void 0 : _tagMap$casinopages3.segment_id, xandrPayload);
              }
            } else if (/^\/(livecasino|play)\/?/i.test(location.pathname)) {
              var _tagMap$livecasinopag, _tagMap$livecasinopag2;
              appendXandrConversionImg(tagMap === null || tagMap === void 0 ? void 0 : (_tagMap$livecasinopag = tagMap.livecasinopages) === null || _tagMap$livecasinopag === void 0 ? void 0 : _tagMap$livecasinopag.pixel_id, xandrPayload);
              if ((tagMap === null || tagMap === void 0 ? void 0 : (_tagMap$livecasinopag2 = tagMap.livecasinopages) === null || _tagMap$livecasinopag2 === void 0 ? void 0 : _tagMap$livecasinopag2.segment_id) !== '') {
                var _tagMap$livecasinopag3;
                appendXandrSegmentImg(tagMap === null || tagMap === void 0 ? void 0 : (_tagMap$livecasinopag3 = tagMap.livecasinopages) === null || _tagMap$livecasinopag3 === void 0 ? void 0 : _tagMap$livecasinopag3.segment_id, xandrPayload);
              }
            } else if (/^\/bingo\/?/i.test(location.pathname)) {
              var _tagMap$bingopages, _tagMap$bingopages2;
              appendXandrConversionImg(tagMap === null || tagMap === void 0 ? void 0 : (_tagMap$bingopages = tagMap.bingopages) === null || _tagMap$bingopages === void 0 ? void 0 : _tagMap$bingopages.pixel_id, xandrPayload);
              if ((tagMap === null || tagMap === void 0 ? void 0 : (_tagMap$bingopages2 = tagMap.bingopages) === null || _tagMap$bingopages2 === void 0 ? void 0 : _tagMap$bingopages2.segment_id) !== '') {
                var _tagMap$bingopages3;
                appendXandrSegmentImg(tagMap === null || tagMap === void 0 ? void 0 : (_tagMap$bingopages3 = tagMap.bingopages) === null || _tagMap$bingopages3 === void 0 ? void 0 : _tagMap$bingopages3.segment_id, xandrPayload);
              }
            } else if (/^\/poker\/?/i.test(location.pathname)) {
              var _tagMap$pokerpages, _tagMap$pokerpages2;
              appendXandrConversionImg(tagMap === null || tagMap === void 0 ? void 0 : (_tagMap$pokerpages = tagMap.pokerpages) === null || _tagMap$pokerpages === void 0 ? void 0 : _tagMap$pokerpages.pixel_id, xandrPayload);
              if ((tagMap === null || tagMap === void 0 ? void 0 : (_tagMap$pokerpages2 = tagMap.pokerpages) === null || _tagMap$pokerpages2 === void 0 ? void 0 : _tagMap$pokerpages2.segment_id) !== '') {
                var _tagMap$pokerpages3;
                appendXandrSegmentImg(tagMap === null || tagMap === void 0 ? void 0 : (_tagMap$pokerpages3 = tagMap.pokerpages) === null || _tagMap$pokerpages3 === void 0 ? void 0 : _tagMap$pokerpages3.segment_id, xandrPayload);
              }
            } else if (/^\/general-info\/whentostop/i.test(location.pathname)) {
              var _tagMap$whentostop;
              if ((tagMap === null || tagMap === void 0 ? void 0 : (_tagMap$whentostop = tagMap.whentostop) === null || _tagMap$whentostop === void 0 ? void 0 : _tagMap$whentostop.segment_id) !== '') {
                var _tagMap$whentostop2;
                appendXandrSegmentImg(tagMap === null || tagMap === void 0 ? void 0 : (_tagMap$whentostop2 = tagMap.whentostop) === null || _tagMap$whentostop2 === void 0 ? void 0 : _tagMap$whentostop2.segment_id, xandrPayload);
              }
            }
          } else if (/deposit/.test(type)) {
            if (type === "firstDeposit") {
              var _tagMap$firstDeposit, _tagMap$firstDeposit2;
              appendXandrConversionImg(tagMap === null || tagMap === void 0 ? void 0 : (_tagMap$firstDeposit = tagMap.firstDeposit) === null || _tagMap$firstDeposit === void 0 ? void 0 : _tagMap$firstDeposit.pixel_id);
              if ((tagMap === null || tagMap === void 0 ? void 0 : (_tagMap$firstDeposit2 = tagMap.firstDeposit) === null || _tagMap$firstDeposit2 === void 0 ? void 0 : _tagMap$firstDeposit2.segment_id) !== '') {
                var _tagMap$firstDeposit3;
                appendXandrSegmentImg(tagMap === null || tagMap === void 0 ? void 0 : (_tagMap$firstDeposit3 = tagMap.firstDeposit) === null || _tagMap$firstDeposit3 === void 0 ? void 0 : _tagMap$firstDeposit3.segment_id);
              }
            } else {
              var _tagMap$furtherDeposi, _tagMap$furtherDeposi2;
              appendXandrConversionImg(tagMap === null || tagMap === void 0 ? void 0 : (_tagMap$furtherDeposi = tagMap.furtherDeposit) === null || _tagMap$furtherDeposi === void 0 ? void 0 : _tagMap$furtherDeposi.pixel_id);
              if ((tagMap === null || tagMap === void 0 ? void 0 : (_tagMap$furtherDeposi2 = tagMap.furtherDeposit) === null || _tagMap$furtherDeposi2 === void 0 ? void 0 : _tagMap$furtherDeposi2.segment_id) !== '') {
                var _tagMap$furtherDeposi3;
                appendXandrSegmentImg(tagMap === null || tagMap === void 0 ? void 0 : (_tagMap$furtherDeposi3 = tagMap.furtherDeposit) === null || _tagMap$furtherDeposi3 === void 0 ? void 0 : _tagMap$furtherDeposi3.segment_id);
              }
            }
          } else if (/registrationSuccessful/i.test(type)) {
            var _tagMap$registrationS4, _tagMap$registrationS5;
            appendXandrConversionImg(tagMap === null || tagMap === void 0 ? void 0 : (_tagMap$registrationS4 = tagMap.registrationSuccessful) === null || _tagMap$registrationS4 === void 0 ? void 0 : _tagMap$registrationS4.pixel_id);
            if ((tagMap === null || tagMap === void 0 ? void 0 : (_tagMap$registrationS5 = tagMap.registrationSuccessful) === null || _tagMap$registrationS5 === void 0 ? void 0 : _tagMap$registrationS5.segment_id) !== '') {
              var _tagMap$registrationS6;
              appendXandrSegmentImg(tagMap === null || tagMap === void 0 ? void 0 : (_tagMap$registrationS6 = tagMap.registrationSuccessful) === null || _tagMap$registrationS6 === void 0 ? void 0 : _tagMap$registrationS6.segment_id);
            }
          }
        }
      }
      function xandrSend(xandrPayload, tagMap, id) {
        var img = document.createElement("img");
        img.height = img.width = 1;
        img.style = "display:none";
        img.src = "https://ib.adnxs.com/pixie?pi=" + id + "&" + xandrPayload + "&script=0";
        document.body.appendChild(img);
      }
      function appendXandrImg(pi, eventName, xandrPayload) {
        if (typeof pi !== "undefined" && pi !== "" && pi !== null) {
          var img = document.createElement("img");
          img.width = img.height = "1";
          img.style = "display:none";
          img.src = "https://ib.adnxs.com/pixie?pi=" + pi + xandrPayload + "&script=0";
          document.body.appendChild(img);
        }
      }
      function appendXandrConversionImg(id, xandrPayload) {
        if (typeof id !== "undefined" && id !== "" && id !== null) {
          var img = document.createElement("img");
          img.width = img.height = "1";
          img.style = "display:none";
          img.src = "https://secure.adnxs.com/px?id=" + id + xandrPayload + "&t=2";
          document.body.appendChild(img);
        }
      }
      function appendXandrSegmentImg(segment_id, xandrPayload) {
        if (typeof segment_id !== "undefined" && segment_id !== "" && segment_id !== null) {
          var img = document.createElement("img");
          img.width = img.height = "1";
          img.style = "display:none";
          img.src = "https://secure.adnxs.com/seg?add=" + xandrPayload + "&t=2";
          document.body.appendChild(img);
        }
      }
      function appendXandrNewConversion(tagMap, type, queryPayload) {
        var img = document.createElement("img");
        img.width = img.height = "1";
        img.style = "display:none";
        img.src = "https://secure.adnxs.com/px?" + queryPayload + "&t=2";
        document.body.appendChild(img);
      }

      //use affiliate params from storage to populate 'channel' & 'campaignId'

      function xandrFireNew(tagMap, type, data) {
        const {
          market,
          currency
        } = useDataLayer();
        let xandrPayload = {};
        let xandrEventLabels = {
          pageView: 'PageView',
          registrationStart: 'RegistrationStart',
          registrationSuccessful: 'RegistrationComplete',
          firstDeposit: 'NewDeposit',
          furtherDeposit: 'FurtherDeposit'
        };
        let userId = getCustomerId(data);
        let country = market;
        let offerStatus = data === null || data === void 0 ? void 0 : data.offerStatus;
        const {
          getMarketingDataUpdated
        } = marketingData();
        let mkData = getMarketingDataUpdated();
        let channel;
        let campaignId;
        try {
          if ((mkData === null || mkData === void 0 ? void 0 : mkData.marketing_channel_id) === "") {
            var params;
            var paramsArray = [];
            var splitParams;
            var arr;
            if (analyticsHelpers.getCookie('affiliate_params') === "") {
              return;
            }
            params = decodeURIComponent(analyticsHelpers.getCookie('affiliate_params'));
            arr = params.split('&');
            for (var i = 0; i < arr.length; i++) {
              splitParams = arr[i].split('=')[1];
              paramsArray.push(splitParams);
            }
            if (mkData) {
              mkData.marketing_channel_id = paramsArray[0] || "";
              mkData.marketing_sub_channel_id = paramsArray[1] || "";
              mkData.marketing_campaign_id = paramsArray[2] || "";
            }
          }
        } catch (error) {
          logToSplunk$1(error, type, data, 'xandrFireNew');
        }
        channel = (mkData === null || mkData === void 0 ? void 0 : mkData.marketing_channel_id) || "";
        campaignId = (mkData === null || mkData === void 0 ? void 0 : mkData.marketing_campaign_id) || "";
        if (/deposit/i.test(type)) {
          let transactionId = (data === null || data === void 0 ? void 0 : data.paymentTransactionId) || "";
          let depositAmount = (data === null || data === void 0 ? void 0 : data.amount) || 0;
          let depositNumber = (data === null || data === void 0 ? void 0 : data.noOfDeposits) || 0;
          let isFirstDeposit;
          if (type === 'firstDeposit') {
            isFirstDeposit = true;
          } else {
            isFirstDeposit = false;
          }
          xandrPayload = {
            name: xandrEventLabels[type],
            user_id: userId,
            TransactionID: transactionId,
            DepositValue: depositAmount,
            //bet_type: ,
            NumberofDeposit: depositNumber,
            //status: ,
            first_deposit: isFirstDeposit,
            country: country,
            currency: currency,
            channel: channel,
            campaignId: campaignId
          };
        } else if (type === 'registrationSuccessful') {
          let regMethod = "";
          let welcomeOfferName = "";
          let welcomeOfferId = "";
          let promoCode = "";
          if (typeof (data === null || data === void 0 ? void 0 : data.registration_method) !== "undefined" && (data === null || data === void 0 ? void 0 : data.registration_method) !== null) {
            regMethod = data === null || data === void 0 ? void 0 : data.registration_method;
          }
          if (typeof (data === null || data === void 0 ? void 0 : data.offerId) !== "undefined" && (data === null || data === void 0 ? void 0 : data.offerId) !== "" && (data === null || data === void 0 ? void 0 : data.offerId) !== null) {
            welcomeOfferName = (data === null || data === void 0 ? void 0 : data.offerName) || "";
            welcomeOfferId = data === null || data === void 0 ? void 0 : data.offerId;
            promoCode = (data === null || data === void 0 ? void 0 : data.promoCode) || "";
          }
          xandrPayload = {
            name: xandrEventLabels[type],
            user_id: userId,
            offer_id: welcomeOfferId,
            offer_name: welcomeOfferName,
            promo_code: promoCode,
            registration_method: regMethod,
            session_id: '',
            offer_status: offerStatus,
            country: country,
            channel: channel,
            campaignId: campaignId
          };
        } else if (type === 'registrationStart') {
          xandrPayload = {
            name: xandrEventLabels[type],
            country: country,
            channel: channel,
            campaignId: campaignId
          };
        } else xandrPayload = {
          name: xandrEventLabels[type]
        };
        if ('pageView' === type && /^(\/(home)?)$/i.test(location.pathname)) {
          //send homepage id specifically
          var img = document.createElement("img");
          img.width = img.height = "1";
          img.style = "display:none";
          img.src = "https://secure.adnxs.com/px?id=" + (tagMap.homepage || "1554228") + "&t=2";
          document.body.appendChild(img);

          //additionally, send a regular pageview
          pixie('event', xandrEventLabels[type]);
          if (tagMap[type]) {
            appendXandrNewConversion();
          }
        } else if ('pageView' === type) {
          pixie('event', xandrEventLabels[type]);
          if (tagMap[type]) {
            appendXandrNewConversion();
          }
        } else {
          xandrPayload.id = tagMap[type];
          pixie('event', xandrEventLabels[type], xandrPayload);
          let queryPayload = Object.entries(xandrPayload).map(_ref2 => {
            let [key, value] = _ref2;
            return `${key}=${value}`;
          }).join("&");
          appendXandrNewConversion(tagMap, type, queryPayload);
        }
      }

      function trafficGuardConfig(id) {
        var dataTrafficGuard = window.dataTrafficGuard = window.dataTrafficGuard || [];
        dataTrafficGuard.push(['property_group_id', id]);

        // Inject TrafficGuard script
        (function () {
          var tg = document.createElement('script');
          tg.type = 'text/javascript';
          tg.async = true;
          tg.src = `//tgtag.io/tg.js?pid=${id}`;
          var s = document.getElementsByTagName('script')[0];
          s.parentNode.insertBefore(tg, s);
        })();

        // Handle no-script case
        var noScriptImg = document.createElement('img');
        noScriptImg.src = `//p.tgtag.io/event?property_group_id=${id}&event_name=pageview&no_script=1`;
        noScriptImg.width = 1;
        noScriptImg.height = 1;
        noScriptImg.border = 0;
        noScriptImg.style.display = 'none';
        document.body.appendChild(noScriptImg);
      }
      function TrafficGuardFire(tagMap, type, data) {
        var dataTrafficGuard = window.dataTrafficGuard = window.dataTrafficGuard || [];
        let eventMapping = {
          'loginSuccess': 'login',
          "registrationSuccessful": "registration",
          "firstDeposit": "purchase"
        };
        let eventType = eventMapping[type];
        if (type == 'pageView') {
          dataTrafficGuard.push(['event', 'pageview']);
        } else {
          let eventId = tagMap[type];
          var params = {
            tag: eventId
          };
          dataTrafficGuard.push(['event', eventType, params]);
        }
      }

      function twitterConfig(id) {
        if (typeof twq !== 'function') {
          !function (e, t, n, s, u, a) {
            e.twq || (s = e.twq = function () {
              s.exe ? s.exe.apply(s, arguments) : s.queue.push(arguments);
            }, s.version = '1.1', s.queue = [], u = t.createElement(n), u.async = !0, u.src = 'https://static.ads-twitter.com/uwt.js', a = t.getElementsByTagName(n)[0], a.parentNode.insertBefore(u, a));
          }(window, document, 'script');
          twq('config', id);
        }
      }
      function twitterFire(tagMap, type, data) {
        if (typeof twq !== 'function') {
          twitterConfig(tagMap.id);
        }
        let depositNumber = (data === null || data === void 0 ? void 0 : data.noOfDeposits) || 0;
        let payload;
        const {
          currency
        } = useDataLayer();
        if (type === 'gameLaunch') {
          payload = {
            'currency': currency,
            'value': depositNumber,
            'contents': data.uniquegameid.split('@')[0]
          };
        } else {
          payload = {
            'currency': currency,
            'value': depositNumber
          };
        }
        const deleteEmpty = ["", 0, null, undefined];
        for (var i in payload) {
          if (deleteEmpty.includes(payload[i])) {
            delete payload[i];
          }
        }
        if (type == 'pageView') {
          twq('event', 'PageView', payload);
        } else {
          let event_id = `tw-${tagMap.id}-${tagMap[type]}`;
          twq('event', event_id, payload);
        }
      }

      function netrefer(id, integrity) {
        return;
      }
      function netreferFire(tagMap, type) {
        var _affiliate_params$spl;
        let data = arguments.length > 2 && arguments[2] !== undefined ? arguments[2] : {};
        let actionName;

        // Get the correct action for the event 
        switch (type) {
          case 'pageView':
            if (window.location.pathname === '/') {
              netrefer(tagMap.id, tagMap.integrity);
            }

            // Check for specific domain and path combinations
            const url = window.location.href;
            if ((url.includes('unibetcasino.be/casino') || url.includes('unibetsports.be/betting/sports/home')) && (window.location.pathname == '/casino' || window.location.pathname == '/betting/sports/home')) {
              netrefer(tagMap.id, tagMap.integrity);
            }
            return;
          case 'firstDeposit':
            actionName = 'FirstTimeDeposit';
            break;
          case 'furtherDeposit':
            actionName = 'Deposit';
            break;
          case 'registrationSuccessful':
            actionName = 'CustomerSignup';
            break;
          default:
            return;
        }
        // Check if customer came from an affilaite    
        let affiliate_params = getMarketingVariablesFromCookie() || {};
        if (Object.keys(affiliate_params).length === 0) {
          return;
        }

        // Get Btag if exists
        let bTag = (_affiliate_params$spl = affiliate_params.split('btag=')[1]) === null || _affiliate_params$spl === void 0 ? void 0 : _affiliate_params$spl.split('&')[0];
        if (bTag == null || bTag === undefined) {
          return;
        }
        let brandID = tagMap.brandID;
        let clientID = "a7e260cd-b4e8-4350-9482-e7ce5bdd0ad6";
        let url = `http://tracking-kindred.netrefer.com/Tracking.svc/Track?to=store&clientID=${clientID}&ActionName=${actionName}&b=${brandID}&s=all&TrackingTag=${bTag}`;
        if (['FirstTimeDeposit', 'Deposit'].includes(actionName)) {
          let depositAmount = (data === null || data === void 0 ? void 0 : data.amount) || '0';
          url += `&DepositAmount=${depositAmount}`;
        }
        try {
          let customerID = getCustomerId(data);
          url += `&customerID=${customerID}`;
        } catch (_unused) {}
        const img = new Image();
        img.src = url;
      }

      function adalyserConfig(id) {
        var _window;
        if (typeof ((_window = window) === null || _window === void 0 ? void 0 : _window.adalyserTracker) !== 'function') {
          (function (windowAlias, documentAlias, trackerName) {
            if (!windowAlias[trackerName]) {
              windowAlias.GlobalAdalyserNamespace = windowAlias.GlobalAdalyserNamespace || [];
              windowAlias.GlobalAdalyserNamespace.push(trackerName);
              windowAlias[trackerName] = function () {
                (windowAlias[trackerName].q = windowAlias[trackerName].q || []).push(arguments);
              };
              windowAlias[trackerName].q = windowAlias[trackerName].q || [];
              var nel = documentAlias.createElement("script"),
                fel = documentAlias.getElementsByTagName("script")[0];
              nel.async = 1;
              nel.src = "//c1.adalyser.com/adalyser.js?cid=" + id;
              fel.parentNode.insertBefore(nel, fel);
            }
          })(window, document, "adalyserTracker");
        }
        let payload = {
          campaignCookieTimeout: 15552000,
          conversionCookieTimeout: 604800,
          clientId: id
        };
        let internalReferrers = ["^(.*\\.)?unibet.co.uk$"];
        if (id === "32red") {
          internalReferrers = ["^(.*\\.)?32red.com$", "^(.*\\.)?32redpoker.com$", "^(.*\\.)?valueactive.eu$", "^(.*\\.)?gameassists.co.uk$", "^(.*\\.)?gameassists.uk$"];
          payload.crossDomainLinker = ["32red.com", "32redpoker.com", "valueactive.eu", "gameassists.co.uk", "gameassists.uk"], payload.useLinkerParams = true;
          payload.trafficSourceInternalReferrers = internalReferrers;
          window.adalyserTracker("create", payload);
          window.adalyserTracker("trackSession", "lce1", {
            a1: "Session"
          });
        } else {
          payload.trafficSourceInternalReferrers = internalReferrers;
          window.adalyserTracker("create", payload);
          window.adalyserTracker("trackSession", "lce1", {});
        }
      }
      function adalyserFire(tagMap, type, data) {
        var _window2;
        if (typeof ((_window2 = window) === null || _window2 === void 0 ? void 0 : _window2.adalyserTracker) !== 'function') {
          adalyserConfig(tagMap.id);
        }
        let userId = getCustomerId(data);
        let depositValue = data === null || data === void 0 ? void 0 : data.amount;
        switch (type) {
          case 'registrationSuccessful':
            window.adalyserTracker("trackEvent", "lce2", {
              uuid: userId
            });
            break;
          case 'firstDeposit':
            window.adalyserTracker("trackEvent", "lce3", {
              uuid: userId,
              value: depositValue,
              a4: "FTD"
            });
            break;
          case 'furtherDeposit':
            window.adalyserTracker("trackEvent", "lce3", {
              uuid: userId,
              value: depositValue,
              a4: "Re-Deposit"
            });
            break;
          case 'gameLaunch':
            window.adalyserTracker("trackEvent", "lce5", {
              uuid: userId,
              a1: data.product
            });
            break;
        }
      }

      function hotJar() {
        (function (h, o, t, j, a, r) {
          h.hj = h.hj || function () {
            (h.hj.q = h.hj.q || []).push(arguments);
          };
          h._hjSettings = {
            hjid: 1821646,
            hjsv: 6
          };
          a = o.getElementsByTagName('head')[0];
          r = o.createElement('script');
          r.async = 1;
          r.src = t + h._hjSettings.hjid + j + h._hjSettings.hjsv;

          // Add error handling to catch script load issues
          r.onerror = function () {};
          r.onload = function () {};
          a.appendChild(r);
        })(window, document, 'https://static.hotjar.com/c/hotjar-', '.js?sv=');
      }

      function spotifyConfig(iD) {
        var _window, _window2;
        if ((_window = window) !== null && _window !== void 0 && _window.spdt && typeof ((_window2 = window) === null || _window2 === void 0 ? void 0 : _window2.spdt) !== 'function') {
          (function (w, d) {
            var id = 'spdt-capture',
              n = 'script';
            if (!d.getElementById(id)) {
              w.spdt = w.spdt || function () {
                (w.spdt.q = w.spdt.q || []).push(arguments);
              };
              var e = d.createElement(n);
              e.id = id;
              e.async = 1;
              e.src = 'https://pixel.byspotify.com/ping.min.js';
              var s = d.getElementsByTagName(n)[0];
              s.parentNode.insertBefore(e, s);
            }
            w.spdt('conf', {
              key: iD
            });
          })(window, document);
        }
      }
      function spotifyFire(tagMap, type, data) {
        let eventLabel = {
          'firstDeposit': 'purchase',
          'furtherDeposit': 'addtocart',
          'registrationSuccessful': 'lead'
        };
        (data === null || data === void 0 ? void 0 : data.noOfDeposits) || 0;
        let depositAmount = (data === null || data === void 0 ? void 0 : data.amount) || 0;
        let transactionId = (data === null || data === void 0 ? void 0 : data.paymentTransactionId) || "";
        let userId = getCustomerId(data);
        switch (type) {
          case 'registrationSuccessful':
            window.spdt(eventLabel[type], {
              category: 'Registration',
              //type: '', // Dynamically populate from session data
              //value: '', // Dynamically populate from session data
              currency: 'AUD'
            });
          case 'firstDeposit':
            window.spdt(eventLabel[type], {
              order_id: transactionId,
              // Dynamically populate from session data
              //discount_code: '', // Dynamically populate from session data
              is_new_customer: userId,
              // Dynamically populate from session data
              value: depositAmount,
              // Dynamically populate from session data
              currency: 'AUD'
            });
            break;
          case 'furtherDeposit':
            window.spdt(eventLabel[type], {
              order_id: transactionId,
              // Dynamically populate from session data
              //discount_code: '', // Dynamically populate from session data
              is_new_customer: userId,
              // Dynamically populate from session data
              value: depositAmount,
              // Dynamically populate from session data
              currency: 'AUD'

              //quantity: '', // Dynamically populate from session data
              //product_id: '', // Dynamically populate from session data
              //product_name: '', // Dynamically populate from session data
              //product_type: '', // Dynamically populate from session data
              //product_vendor: '', // Dynamically populate from session data
              //variant_id: '', // Dynamically populate from session data
              //variant_name: '', // Dynamically populate from session data
            });
            break;
          default:
            return;
        }
      }

      function tradeDeskConfig(advertiserId, pixelIds, ga4MeasurementId) {
        window.ttdConversionEventsLayer = window.ttdConversionEventsLayer || [];
        if (typeof ttdConversionEvents !== 'function') {
          window.ttdConversionEvents = function () {
            window.ttdConversionEventsLayer.push(arguments);
          };
          var script = document.createElement('script');
          script.async = true;
          script.src = 'https://js.adsrvr.org/up_loader.3.0.0.js';
          var firstScript = document.getElementsByTagName('script')[0];
          firstScript.parentNode.insertBefore(script, firstScript);
        }
        ttdConversionEvents('init', {
          advertiserId: advertiserId,
          pixelIds: pixelIds,
          ga4MeasurementId: ga4MeasurementId
        });
      }
      function tradeDeskFire(tagMap, type, data) {
        if (typeof ttdConversionEvents !== 'function') {
          tradeDeskConfig(tagMap.advertiserId, tagMap.pixelIds, tagMap.ga4MeasurementId);
        }
        const {
          currency
        } = useDataLayer();
        const payload = {
          adv: tagMap.advertiserId,
          pixel_ids: tagMap.pixelIds
        };
        if (type === 'registrationSuccessful') {
          payload.td1 = "registrationSuccessful";
        }
        if (type === 'firstDeposit') {
          payload.td2 = "firstDeposit";
          payload.currency = currency;
          if ((data === null || data === void 0 ? void 0 : data.amount) != null) payload.value = data.amount;
        }
        if (type === 'furtherDeposit') {
          payload.td3 = "furtherDeposit";
          payload.currency = currency;
          if ((data === null || data === void 0 ? void 0 : data.amount) != null) payload.value = data.amount;
        }
        ttdConversionEvents('event', payload);
      }

      function marketingEvents() {
        let eventList = ['pageView', 'depositCompleted', 'registrationStart', 'registrationSuccessful', 'loginSuccess', 'gameLaunch', 'addBet', 'placeBet', 'genericBannerInteraction'];
        return eventList;
      }
      function marketingHandler(type, data) {
        const {
          isApp
        } = useDataLayer();
        if (type === 'registrationSuccessful' && (data === null || data === void 0 ? void 0 : data.registration_method) === 'simplified') {
          return;
        }
        const getMappedTags = async () => {
          return await marketingMap();
        };
        const mappedTagsList = getMappedTags();
        let pendingEvents = analyticsHelpers.storageManagement._getStorage("sessionStorage", "pendingPixelEvents");
        // first we initiate the tag configs
        if (/^pageView$|^OTConsentApplied$/.test(type) && getMarketingConsent()) {
          mappedTagsList.then(mappedTags => {
            const ga4_environment = /\-/.test(window.location.hostname.split('.')[0]) ? "dev" : "prod";
            try {
              if (mappedTags.bing.id) {
                bingConfig(mappedTags.bing.id);
              }
            } catch (error) {
              logToSplunk$1(error, type, data, 'bingConfig');
            }
            // Google Start 
            try {
              if (mappedTags.adwords.id) {
                googleConfig(mappedTags.adwords.id);
              }
            } catch (error) {
              logToSplunk$1(error, type, data, 'googleConfig-adwords');
            }
            try {
              if (mappedTags.cm360.id) {
                googleConfig(mappedTags.cm360.id);
              }
            } catch (error) {
              logToSplunk$1(error, type, data, 'googleConfig-cm360');
            }
            try {
              let ga4_id = mappedTags.ga4.id;
              if (typeof ga4_id === 'string') {
                ga4_id = {
                  prod: ga4_id,
                  dev: ga4_id
                };
              }
              if (ga4_id && ga4_id[ga4_environment]) {
                googleConfig(ga4_id[ga4_environment]);
              }
            } catch (error) {
              logToSplunk$1(error, type, data, 'googleConfig-ga4');
            }
            try {
              if (mappedTags.adwordsYoutube.id) {
                googleConfig(mappedTags.adwordsYoutube.id);
              }
            } catch (error) {
              logToSplunk$1(error, type, data, 'googleConfig-adwordsYoutube');
            }
            //Google end 
            try {
              if (mappedTags.meta.id && mappedTags.meta.id[0] !== "") {
                let ids = mappedTags.meta.id;
                for (let i = 0; i < ids.length; i++) {
                  metaConfig(ids[i], data);
                }
              }
            } catch (error) {
              logToSplunk$1(error, type, data, 'metaConfig');
            }
            try {
              if (mappedTags.snapchat.id) {
                snapchatConfig(mappedTags.snapchat.id);
              }
            } catch (error) {
              logToSplunk$1(error, type, data, 'snapchatConfig');
            }
            try {
              if (mappedTags.spotify.id) {
                spotifyConfig(mappedTags.spotify.id);
              }
            } catch (error) {
              logToSplunk$1(error, type, data, 'spotifyConfig');
            }
            try {
              if (mappedTags.reddit.id) {
                redditConfig(mappedTags.reddit.id);
              }
            } catch (error) {
              logToSplunk$1(error, type, data, 'redditConfig');
            }
            try {
              if (mappedTags.twitter.id) {
                twitterConfig(mappedTags.twitter.id);
              }
            } catch (error) {
              logToSplunk$1(error, type, data, 'twitterConfig');
            }
            try {
              if (mappedTags.xandr.id) {
                xandrConfig(mappedTags.xandr.id);
              }
            } catch (error) {
              logToSplunk$1(error, type, data, 'xandrConfig');
            }
            try {
              if (mappedTags.trafficGuard.id) {
                trafficGuardConfig(mappedTags.trafficGuard.id);
              }
            } catch (error) {
              logToSplunk$1(error, type, data, 'trafficGuardConfig');
            }
            try {
              if (mappedTags.adalyser.id) {
                adalyserConfig(mappedTags.adalyser.id);
              }
            } catch (error) {
              logToSplunk$1(error, type, data, 'adalyserConfig');
            }
            try {
              if (mappedTags.tradeDesk && mappedTags.tradeDesk.advertiserId) {
                let ga4MeasurementId = mappedTags.tradeDesk.ga4MeasurementId;
                if (typeof ga4MeasurementId === 'object') {
                  ga4MeasurementId = ga4MeasurementId[ga4_environment];
                }
                tradeDeskConfig(mappedTags.tradeDesk.advertiserId, mappedTags.tradeDesk.pixelIds, ga4MeasurementId);
              }
            } catch (error) {
              logToSplunk$1(error, type, data, 'tradeDeskConfig');
            }
          });
          if (pendingEvents !== "" && pendingEvents !== undefined) {
            let parsedEvent = JSON.parse(pendingEvents);
            marketingHandler(parsedEvent.type, parsedEvent.data);
            analyticsHelpers.storageManagement._setStorage("sessionStorage", "pendingPixelEvents", "");
          }
        }
        if (type === 'depositCompleted') {
          if (parseInt(data.noOfDeposits) === 1) {
            type = 'firstDeposit';
          } else {
            type = 'furtherDeposit';
          }
        }

        // If there are pending events during registration, we defer them
        //if(getMarketingConsent() && ((type === 'registrationSuccessful'||type === 'genericBannerInteraction') && (pendingEvents === ""||pendingEvents === undefined))){
        if (getMarketingConsent() && type === 'genericBannerInteraction' && (pendingEvents === "" || pendingEvents === undefined)) {
          let pendingDetail = {
            type: type,
            data: data
          };
          let stringPendingDetails = JSON.stringify(pendingDetail);
          analyticsHelpers.storageManagement._setStorage("sessionStorage", "pendingPixelEvents", stringPendingDetails);
        } else {
          // Pixels that fire with marketing consent
          if (getMarketingConsent()) {
            mappedTagsList.then(mappedTags => {
              const ga4_environment = /\-/.test(window.location.hostname.split('.')[0]) ? "dev" : "prod";
              //tag firing
              try {
                for (let i = 0; i < mappedTags.adform.ids.length; i++) {
                  if (mappedTags.adform.ids[i].id && mappedTags.adform.ids[i].eventList.includes(type)) {
                    adformFire(mappedTags.adform.ids[i], type, data);
                  }
                }
              } catch (error) {
                logToSplunk$1(error, type, data, 'adformFire');
              }
              try {
                if (mappedTags.bing.id && mappedTags.bing.eventList.includes(type)) {
                  bingFire(mappedTags.bing, type, data);
                }
              } catch (error) {
                logToSplunk$1(error, type, data, 'bingFire');
              }
              // Google Start 
              try {
                if (mappedTags.adwords.id && mappedTags.adwords.eventList.includes(type)) {
                  googleFire(mappedTags.adwords, type, data, 'adwords');
                }
              } catch (error) {
                logToSplunk$1(error, type, data, 'googleAdwordsFire-adwords');
              }
              try {
                if (mappedTags.adwordsYoutube.id && mappedTags.adwordsYoutube.eventList.includes(type)) {
                  googleFire(mappedTags.adwordsYoutube, type, data, 'adwords');
                }
              } catch (error) {
                logToSplunk$1(error, type, data, 'googleAdwordsFire-adwordsYoutube');
              }
              try {
                if (mappedTags.cm360.id && mappedTags.cm360.eventList.includes(type)) {
                  googleFire(mappedTags.cm360, type, data, 'cm360');
                }
              } catch (error) {
                logToSplunk$1(error, type, data, 'googleFire-cm360');
              }
              try {
                let ga4_id = mappedTags.ga4.id;
                if (typeof ga4_id === 'string') {
                  ga4_id = {
                    prod: ga4_id,
                    dev: ga4_id
                  };
                }
                if (ga4_id && ga4_id[ga4_environment] && mappedTags.ga4.eventList.includes(type)) {
                  googleFire({
                    id: ga4_id[ga4_environment],
                    eventList: mappedTags.ga4.eventList
                  }, type, data, 'ga4');
                }
              } catch (error) {
                logToSplunk$1(error, type, data, 'googleFire-ga4');
              }
              //Google end 
              try {
                if (mappedTags.meta.id && mappedTags.meta.id[0] !== "" && mappedTags.meta.eventList.includes(type)) {
                  let ids = mappedTags.meta.id;
                  for (let i = 0; i < ids.length; i++) {
                    metaFire(ids[i], type, data);
                  }
                }
              } catch (error) {
                logToSplunk$1(error, type, data, 'metaFire');
              }
              try {
                if (mappedTags.snapchat.id && mappedTags.snapchat.eventList.includes(type)) {
                  snapchatFire(mappedTags.snapchat, type, data);
                }
              } catch (error) {
                logToSplunk$1(error, type, data, 'snapchatFire');
              }
              try {
                if (mappedTags.reddit.id && mappedTags.reddit.eventList.includes(type)) {
                  redditFire(mappedTags.reddit, type, data);
                }
              } catch (error) {
                logToSplunk$1(error, type, data, 'redditFire');
              }
              try {
                if (mappedTags.twitter.id && mappedTags.twitter.eventList.includes(type)) {
                  twitterFire(mappedTags.twitter, type, data);
                }
              } catch (error) {
                logToSplunk$1(error, type, data, 'twitterFire');
              }
              try {
                if (mappedTags.xandr.id && mappedTags.xandr.eventList.includes(type)) {
                  if (mappedTags.xandr.method === 'new') {
                    xandrFireNew(mappedTags.xandr, type, data);
                  } else {
                    xandrFire(mappedTags.xandr, type, data);
                  }
                }
              } catch (error) {
                logToSplunk$1(error, type, data, 'xandrFire');
              }
              try {
                if (mappedTags.trafficGuard.id && mappedTags.trafficGuard.eventList.includes(type)) {
                  TrafficGuardFire(mappedTags.trafficGuard, type, data);
                }
              } catch (error) {
                logToSplunk$1(error, type, data, 'TrafficGuardFire');
              }
              try {
                if (mappedTags.adalyser.id && mappedTags.adalyser.eventList.includes(type)) {
                  adalyserFire(mappedTags.adalyser, type, data);
                }
              } catch (error) {
                logToSplunk$1(error, type, data, 'adalyserFire');
              }
              try {
                if (mappedTags.spotify.id && mappedTags.spotify.eventList.includes(type)) {
                  spotifyFire(mappedTags.spotify, type, data);
                }
              } catch (error) {
                logToSplunk$1(error, type, data, 'spotifyFire');
              }
              try {
                if (mappedTags.tradeDesk && mappedTags.tradeDesk.advertiserId && mappedTags.tradeDesk.eventList.includes(type)) {
                  let tradeDeskTagMap = mappedTags.tradeDesk;
                  if (typeof tradeDeskTagMap.ga4MeasurementId === 'object') {
                    tradeDeskTagMap = _objectSpread2(_objectSpread2({}, tradeDeskTagMap), {}, {
                      ga4MeasurementId: tradeDeskTagMap.ga4MeasurementId[ga4_environment]
                    });
                  }
                  tradeDeskFire(tradeDeskTagMap, type, data);
                }
              } catch (error) {
                logToSplunk$1(error, type, data, 'tradeDeskFire');
              }
            });
          }
        }
        // Pixels that fire without marketing consent (affiliates & surveys)
        mappedTagsList.then(mappedTags => {
          try {
            if (mappedTags && mappedTags.netrefer.id && mappedTags.netrefer.eventList.includes(type) && !isApp) {
              netreferFire(mappedTags.netrefer, type, data);
            }
          } catch (error) {
            logToSplunk$1(error, type, data, 'netreferFire');
          }
          try {
            if (/www(-(qa1|si1|pt))?\.32red\.com/i.test(window.location.hostname) && !isApp) {
              hotJar();
            }
          } catch (error) {
            logToSplunk$1(error, type, data, 'hotJar');
          }
        });
      }

      /*import { Helmet } from 'kwp-seo';
      import React, { useEffect } from 'react';*/

      function snowplowSetAnalyticsEvents() {
        var waitForOneTrust = function () {
          let webAn = JSON.parse(sessionStorage.getItem("webAnalytics") || "{}");
          if (OneTrust.IsAlertBoxClosed() == false) {
            if (!webAn["snowplowenhConsInitVisibleOnce"]) {
              webAn["snowplowenhConsInitVisibleOnce"] = true;
              try {
                sessionStorage.setItem("webAnalytics", JSON.stringify(webAn));
              } catch (e) {}
              window.snowplow("trackCmpVisible:" + webAn["spVersion"], {
                elapsedTime: performance.now()
              });
            }
          }
        };
        var waitForOneTrustTimeout = function () {
          if (typeof OneTrust != "undefined") waitForOneTrust();else setTimeout(waitForOneTrustTimeout, 300);
        };
        waitForOneTrustTimeout();
      }

      /*export const getCookieConsentId = () => {
              //const kindredEnvironment = window?.env?.environment; // dev or prod
          useEffect(() => {
              let domain = location.hostname;
              let cookieConsentId = null;
              const oneTrustMapping = [
                  {'domainName':/fi(\-(si|qa)1)?\.bingo\.com/g,'id':'018e4206-95f8-7878-9a10-c1411e9a9338'},
                  {'domainName':/uk(\-(si|qa)1)?\.bingo\.com/g,'id':'8dc1eb71-cbde-466b-bd81-3d251c28a3d1'},
                  {'domainName':/int(\-(si|qa)1)?\.32red\.com/g,'id':'ced37516-ee9a-459c-96a1-c15ec2bd1f49'},
                  {'domainName':/hu(\-(si|qa)1)?\.32red\.com/g,'id':'f2e5b5b5-7620-47df-96cf-d1384b114567'},
                  {'domainName':/(\-(si|qa)1)?\.ottocasino\.se/g,'id':'018e5c4d-3c78-7138-a51d-b817fe11f5af'}
              ]
              for (const mapping of oneTrustMapping) {
                  if (mapping.domainName.test(domain)) {
                    let prefix = ''
                    if (/qa1|si1/.test(domain)) {
                      prefix='-test';
                    }
                    cookieConsentId=mapping.id+prefix;
                  }
              }
              if(cookieConsentId){
                  let onetrustScript = document.createElement('script');
                  onetrustScript.type="text/javascript";
                  onetrustScript.setAttribute('data-domain-script',cookieConsentId); 
                  onetrustScript.setAttribute('data-document-language',true)
                  onetrustScript.async=1;
                  onetrustScript.src = 'https://cdn-ukwest.onetrust.com/scripttemplates/otSDKStub.js'
                  let g=document.head.getElementsByTagName('script')[0];
                  g.parentNode.insertBefore(onetrustScript,g);
                }
          }, []);
          return (<Helmet>
              <script type="text/javascript" data-analytics='init-cookie'>console.log("GOall")</script>
          </Helmet>);

      }*/

      function initializeSnowplow(library_location, library_path) {
        (function (p, l, o, w, i, n, g) {
          if (!p[i]) {
            p.GlobalSnowplowNamespace = p.GlobalSnowplowNamespace || [];
            p.GlobalSnowplowNamespace.push(i);
            p[i] = function () {
              (p[i].q = p[i].q || []).push(arguments);
            };
            p[i].q = p[i].q || [];
            n = l.createElement(o);
            g = l.getElementsByTagName(o)[0];
            n.async = 1;
            n.src = w;
            g.parentNode.insertBefore(n, g);
          }
        })(window, document, "script", "https://" + library_location + "/kindred_snow/" + library_path, "snowplow");
      }
      function handleCrossDomainLinks(linkElement) {
        let linkHostName = linkElement;
        if (/^#/.test(linkElement.getAttribute("href"))) {
          return false;
        }
        if (/(QA1|SI1|PT1)/i.test(window.location.hostname)) {
          return false;
        }
        if (/unibet(casino|sports|games)?\.be/i.test(window.location.hostname)) {
          linkHostName = linkElement.hostname;
        }
        return /(?:pl|hu)\.unibet-\d+\.com|unibet(casino|sports|games)?\.be|welcome\d*\.unibet\.com|www\.unibetcommunity\.com/i.test(linkHostName);
      }
      function initSnowplow() {
        let library_location = location.hostname;
        let library_path = 's3.13.1/kindred_s.js';
        const {
          isApp
        } = useDataLayer();
        // These are the urls that we not want to initialize snowplow on
        const nonWhitelistedUrls = [/ca.unibet.com/i, /(www|hu)(-(qa1|si1|pt1|prod))?.boabet(-\d+)?\.com/i];
        if (typeof window._snowplow_has_been_initialize == "undefined" && !nonWhitelistedUrls.some(url => url.test(location.hostname))) {
          if (isApp) {
            library_path = "s0.2.0/mobile_webview_s.js";
          }

          // First we're ensuring that the library_location is the correct one for the collector endpoint
          const locationMapping = {
            'unibet.com.au': /unibet.com.au/i,
            'www.unibet.com': /(hu1|fi|de)(-(qa1|si1))?\.unibet\.com/i
          };
          for (const [mappedLocation, pattern] of Object.entries(locationMapping)) {
            if (pattern.test(library_location)) {
              library_location = mappedLocation;
              break;
            }
          }

          // Then we're initializing the snowplow tracker
          window._snowplow_has_been_initialize = "1";
          initializeSnowplow(library_location, library_path);
          function snowplowWebTracker() {
            // Add enhanced consent tracking plugin
            const CONSENT_PLUGIN_URL = 'https://cdn.jsdelivr.net/npm/@snowplow/browser-plugin-enhanced-consent@latest/dist/index.umd.min.js';
            window.snowplow('addPlugin', CONSENT_PLUGIN_URL, ['snowplowEnhancedConsentTracking', 'EnhancedConsentPlugin']);

            // Default QA endpoint and configs
            let collector_endpoint = 'https://com-kindredgroup-qa1.collector.snplow.net';
            let spVersion = 'sp1';

            // Base tracker configuration
            const configs = {
              appId: 'web',
              discoverRootDomain: true,
              cookieSameSite: 'Lax',
              eventMethod: 'post',
              contexts: {
                performanceTiming: true,
                session: true
              },
              crossDomainLinker: handleCrossDomainLinks
            };

            // Update endpoint and version for production
            if (/si1/.test(location.hostname)) {
              // Initialize the tracker on SI1 
              collector_endpoint = "com-kindredgroup-prod1.mini.snplow.net";
              spVersion = 'sp';
            } else if (!/qa1|si1/.test(location.hostname)) {
              // Initialize the tracker on production
              collector_endpoint = location.hostname;
              spVersion = 'sp';
              configs.postPath = "/tp2";
            }
            let webAn = JSON.parse(sessionStorage.getItem("webAnalytics") || "{}");
            webAn["spVersion"] = spVersion;
            try {
              sessionStorage.setItem("webAnalytics", JSON.stringify(webAn));
            } catch (e) {}
            window.snowplow('newTracker', spVersion, collector_endpoint, configs);
            window.addEventListener('OneTrustGroupsUpdated', e => {
              snowplowSetAnalyticsEvents();
            });
          }
          if (!isApp) {
            snowplowWebTracker();
          }
        }
      }

      class ValidationError extends Error {
        constructor(field, message, value) {
          super(field + ': ' + message);
          this.field = field;
          this.value = value;
          this.name = 'ValidationError';
          // This is needed for instanceof to work correctly
          Object.setPrototypeOf(this, ValidationError.prototype);
        }
      } exports('d', ValidationError);

      const AFFILIATE = 'affiliate';
      const NATURAL_SEARCH = 'natural_search';
      const NATURAL_SOCIAL = 'natural_social';
      const REFERRING_DOMAIN = 'referring_domains';
      const SATELLITE_SITE = 'satellite_site';
      // Only domains present in the lists will activate their respective channels
      const DOMAINS_NATURAL_SEARCH = ['www.google.', 'bing.', 'search.yahoo.', 'search.seznam.', '.yandex.', '.ask.'];
      const DOMAINS_NATURAL_SOCIAL = ['facebook.com', 't.co', 'pinterest.', 'linked.com', 'plus.google', 'instagram.com', 'hootsuite.com'];
      // Exclusion list: domains that are considered internal
      let DOMAINS_REFERRING = ['.unibet.', '.bingo.', '.vladcazino.', '.highroller.', '.highrolling.', '.storspelare.', '.storspiller.', '.igame.', '.casinohuone.', '.kolikkopelit.', '.mariacasino.', 'paypal.com', 'merchant.itsme', '.32red.', '.ottokasino', '.ottocasino.'];
      const IDIN_DOMAINS = ['diensten.snsbank.nl', '.abnamro.nl', 'diensten.asnbank.nl', 'idin.bunq.com', 'ideal.ing.nl', 'idp.rabobank.nl', 'diensten.regiobank.nl', 'diensten.snsbank.nl'];
      const METID_NEMID = ['unibet.criipto.id', 'unibet.mitid.dk'];
      DOMAINS_REFERRING = DOMAINS_REFERRING.concat(IDIN_DOMAINS).concat(METID_NEMID);
      const analyticsHelpers = exports('a', {
        shouldLog() {
          return localStorage.getItem('kwp-analytics-show-logs') === 'true';
        },
        pageOrSite() {
          var _window;
          // Existing sites use "site", newer sites use "page"
          // Mariacasino has "site" and "page" so extra condition for when both exist
          const {
            page,
            site
          } = ((_window = window) === null || _window === void 0 ? void 0 : _window.analytics_datalayer) || {};
          if (page !== null && page !== void 0 && page.jurisdiction) return page;
          if (site !== null && site !== void 0 && site.jurisdiction) return site;
          return page || site || {};
        },
        setCookie: (name, value, days) => {
          let expires = '';
          if (days) {
            const date = new Date();
            date.setTime(date.getTime() + days * 24 * 60 * 60 * 1000);
            expires = '; expires=' + date.toUTCString();
          }
          const domainName = window.location.hostname.split('.').splice(1).join('.');
          document.cookie = name + '=' + (encodeURIComponent(value) || '') + expires + '; path=/;domain=' + domainName;
        },
        deleteCookie: name => {
          document.cookie = name + '=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=' + window.location.hostname.split('.').splice(1).join('.');
        },
        getCookie: name => {
          const value = '; ' + document.cookie;
          const parts = value.split('; ' + name + '=');
          if (parts.length === 2) return decodeURI(parts.pop().split(';').shift());
        },
        getTrackingCode: () => {
          const url = window.location.href;
          let campaignTrackingCode = '';
          const getQueryString = field => {
            const reg = new RegExp('[?&]' + field + '=([^&#]*)', 'i');
            const string = reg.exec(url);
            return string ? string[1] : null;
          };
          const isReferrerPopunder = document.referrer.indexOf('/pop/') > -1 ? true : false;
          const isMktid = url.indexOf('mktid') > -1 ? true : false;
          const isCid = url.indexOf('cid') > -1 ? true : false;
          const isUtm = url.indexOf('utm_medium') > -1 ? true : false;
          if (isMktid) {
            campaignTrackingCode = getQueryString('mktid');
          } else if (isCid) {
            campaignTrackingCode = getQueryString('cid');
          } else if (isUtm) {
            const medium = getQueryString('utm_medium');
            const source = getQueryString('utm_source') || 'NONE';
            const content = getQueryString('utm_content') || 'NONE';
            const campaign = getQueryString('utm_campaign') || 'NONE';
            const term = getQueryString('utm_term') || 'NONE';
            campaignTrackingCode = medium + ':' + source + ':' + content + ':' + campaign + ':' + term;
          }
          if (isReferrerPopunder) {
            const referrerUrl = document.referrer;
            const isReferrerMktid = referrerUrl.indexOf('mktid') > -1 ? true : false;
            const isReferrerCid = referrerUrl.indexOf('cid') > -1 ? true : false;
            if (isReferrerMktid) {
              campaignTrackingCode = getQueryString('mktid').replace('1:', 'popunder:');
            } else if (isReferrerCid) {
              campaignTrackingCode = getQueryString('cid').replace('1:', 'popunder:');
            }
          }
          return campaignTrackingCode;
        },
        getBrand: () => {
          return (analyticsHelpers.pageOrSite().brand || '').replace(/bingo_com/i, 'bingo');
        },
        getMarket: () => {
          let market = (analyticsHelpers.pageOrSite().jurisdiction || 'all').toLowerCase();
          if (market === 'mt') {
            market = analyticsHelpers.getShortCode();
            let market_exceptions = {
              'int.32red.com': 'int',
              'int-qa1.32red.com': 'int',
              'int-si1.32red.com': 'int',
              'www.bingo.com': 'int',
              'www-qa1.bingo.com': 'int',
              'www-si1.bingo.com': 'int',
              'en.casinohuone.com': 'int',
              'en-qa1.casinohuone.com': 'int',
              'en-si1.casinohuone.com': 'int',
              'en.kolikkopelit.com': 'int',
              'en-qa1.kolikkopelit.com': 'int',
              'en-si1.kolikkopelit.com': 'int',
              'www.mariacasino.com': 'int',
              'www-qa1.mariacasino.com': 'int',
              'www-si1.mariacasino.com': 'int',
              'en.ottokasino.com': 'int',
              'en-qa1.ottokasino.com': 'int',
              'en-si1.ottokasino.com': 'int',
              'www.unibet.be': 'be',
              'www-qa1.unibet.be': 'be',
              'www-si1.unibet.be': 'be',
              'www.unibet.com': 'int',
              'www-qa1.unibet.com': 'int',
              'www-si1.unibet.com': 'int'
            };
            let market_overwrite = market_exceptions[document.location.hostname];
            if (market_overwrite !== undefined) {
              market = market_overwrite;
            }

            //fix for gr.unibet-3.com
            if (market === 'el') {
              market = 'gr';
            }
          }
          return market;
        },
        getDeviceChannel: () => {
          // marked for deletion and use directly the analytics datalayer reference
          return (analyticsHelpers.pageOrSite().channel || '').toLowerCase();
        },
        getJurisdiction: () => {
          // marked for deletion and use directly the analytics datalayer reference
          return (analyticsHelpers.pageOrSite().jurisdiction || '').toLowerCase();
        },
        getOddsFormat: () => {
          var _ref, _JSON$parse, _localStorage, _localStorage2;
          // marked for deletion and use directly the analytics datalayer reference
          return ((_ref = ((_JSON$parse = JSON.parse((_localStorage = localStorage) === null || _localStorage === void 0 ? void 0 : _localStorage.getItem('key_user_setting'))) === null || _JSON$parse === void 0 ? void 0 : _JSON$parse.oddsFormat) || ((_localStorage2 = localStorage) === null || _localStorage2 === void 0 ? void 0 : _localStorage2.getItem('ksp_oddsformat'))) === null || _ref === void 0 ? void 0 : _ref.toLowerCase()) || '';
        },
        getCountryCode: () => {
          var _analyticsHelpers$pag;
          // marked for deletion and use directly the analytics datalayer reference
          return (((_analyticsHelpers$pag = analyticsHelpers.pageOrSite().language) === null || _analyticsHelpers$pag === void 0 ? void 0 : _analyticsHelpers$pag.countryCode) || analyticsHelpers.pageOrSite().market || '').toLowerCase();
        },
        getShortCountryCode: () => {
          var _analyticsHelpers$pag2;
          // marked for deletion and use directly the analytics datalayer reference
          return (((_analyticsHelpers$pag2 = analyticsHelpers.pageOrSite().language) === null || _analyticsHelpers$pag2 === void 0 ? void 0 : _analyticsHelpers$pag2.shortCountryCode) || '').toLowerCase();
        },
        getShortCode: () => {
          var _analyticsHelpers$pag3;
          // marked for deletion and use directly the analytics datalayer reference
          return (((_analyticsHelpers$pag3 = analyticsHelpers.pageOrSite().language) === null || _analyticsHelpers$pag3 === void 0 ? void 0 : _analyticsHelpers$pag3.split('_')[0]) || analyticsHelpers.pageOrSite().market.split('_')[0] || '').toLowerCase();
        },
        getTimeZone: () => {
          var _analyticsHelpers$pag4;
          // marked for deletion and use directly the analytics datalayer reference
          return (((_analyticsHelpers$pag4 = analyticsHelpers.pageOrSite().language) === null || _analyticsHelpers$pag4 === void 0 ? void 0 : _analyticsHelpers$pag4.timeZone) || '').toLowerCase();
        },
        getPlayForFunRequiresLogin: () => {
          // marked for deletion and use directly the analytics datalayer reference
          return analyticsHelpers.pageOrSite().playForFunRequiresLogin || false;
        },
        getMarketingChannelId: () => {
          const urlParams = new URLSearchParams(window.location.search);
          return urlParams.has('ch') ? urlParams.get('ch') : '';
        },
        getDeviceGroup: () => {
          var _window2, _window2$analytics_da, _window2$analytics_da2;
          // marked for deletion and use directly the analytics datalayer reference
          return (((_window2 = window) === null || _window2 === void 0 ? void 0 : (_window2$analytics_da = _window2.analytics_datalayer) === null || _window2$analytics_da === void 0 ? void 0 : (_window2$analytics_da2 = _window2$analytics_da.device) === null || _window2$analytics_da2 === void 0 ? void 0 : _window2$analytics_da2.group) || '').toLowerCase();
        },
        getDeviceOs: () => {
          var _window3, _window3$analytics_da, _window3$analytics_da2;
          // marked for deletion and use directly the analytics datalayer reference
          return (((_window3 = window) === null || _window3 === void 0 ? void 0 : (_window3$analytics_da = _window3.analytics_datalayer) === null || _window3$analytics_da === void 0 ? void 0 : (_window3$analytics_da2 = _window3$analytics_da.device) === null || _window3$analytics_da2 === void 0 ? void 0 : _window3$analytics_da2.os) || '').toLowerCase();
        },
        getDeviceOsVersion: () => {
          var _window4, _window4$analytics_da, _window4$analytics_da2;
          // marked for deletion and use directly the analytics datalayer reference
          return (((_window4 = window) === null || _window4 === void 0 ? void 0 : (_window4$analytics_da = _window4.analytics_datalayer) === null || _window4$analytics_da === void 0 ? void 0 : (_window4$analytics_da2 = _window4$analytics_da.device) === null || _window4$analytics_da2 === void 0 ? void 0 : _window4$analytics_da2.osVersion) || '').toLowerCase();
        },
        getAppVersion: () => {
          let version = '';
          let clientId = new URLSearchParams(window.location.search.toLowerCase()).get('clientid'); //clientId=unibetpro_mobilephone-ios_5.58.0
          if (clientId) {
            let parts = clientId.split('_');
            if (/^(\d+)\.(\d+)\.(\d+)$/.test(parts[2])) version = parts[2];
          }
          if (analyticsHelpers.isPWA()) {
            version = 'pwa';
          }
          return version;
        },
        getApplicationId: () => {
          var _window5, _window5$analytics_da, _window5$analytics_da2;
          if ((_window5 = window) !== null && _window5 !== void 0 && (_window5$analytics_da = _window5.analytics_datalayer) !== null && _window5$analytics_da !== void 0 && (_window5$analytics_da2 = _window5$analytics_da.page) !== null && _window5$analytics_da2 !== void 0 && _window5$analytics_da2.isKwp) {
            return 'kwp';
          } else {
            var _window6, _window6$analytics_da, _window6$analytics_da2;
            return (_window6 = window) === null || _window6 === void 0 ? void 0 : (_window6$analytics_da = _window6.analytics_datalayer) === null || _window6$analytics_da === void 0 ? void 0 : (_window6$analytics_da2 = _window6$analytics_da.device) === null || _window6$analytics_da2 === void 0 ? void 0 : _window6$analytics_da2.applicationId;
          }
        },
        isApp: () => {
          var _window7, _window7$analytics_da, _window7$analytics_da2;
          return ((_window7 = window) === null || _window7 === void 0 ? void 0 : (_window7$analytics_da = _window7.analytics_datalayer) === null || _window7$analytics_da === void 0 ? void 0 : (_window7$analytics_da2 = _window7$analytics_da.device) === null || _window7$analytics_da2 === void 0 ? void 0 : _window7$analytics_da2.isApp) || false;
        },
        getClientId: () => {
          var _window8, _window8$analytics_da, _window8$analytics_da2;
          return ((_window8 = window) === null || _window8 === void 0 ? void 0 : (_window8$analytics_da = _window8.analytics_datalayer) === null || _window8$analytics_da === void 0 ? void 0 : (_window8$analytics_da2 = _window8$analytics_da.device) === null || _window8$analytics_da2 === void 0 ? void 0 : _window8$analytics_da2.clientId) || '';
        },
        getCustomerId: () => {
          var _window9, _window9$analytics_da, _window9$analytics_da2;
          return ((_window9 = window) === null || _window9 === void 0 ? void 0 : (_window9$analytics_da = _window9.analytics_datalayer) === null || _window9$analytics_da === void 0 ? void 0 : (_window9$analytics_da2 = _window9$analytics_da.user) === null || _window9$analytics_da2 === void 0 ? void 0 : _window9$analytics_da2.customerId) || 0;
        },
        getCurrency: () => {
          var _window10, _window10$analytics_d, _window10$analytics_d2, _window11, _window11$analytics_d, _window11$analytics_d2, _window11$analytics_d3, _window12, _window12$cms, _window12$cms$site, _window12$cms$site$cu;
          return ((_window10 = window) === null || _window10 === void 0 ? void 0 : (_window10$analytics_d = _window10.analytics_datalayer) === null || _window10$analytics_d === void 0 ? void 0 : (_window10$analytics_d2 = _window10$analytics_d.page) === null || _window10$analytics_d2 === void 0 ? void 0 : _window10$analytics_d2.currency) || ((_window11 = window) === null || _window11 === void 0 ? void 0 : (_window11$analytics_d = _window11.analytics_datalayer) === null || _window11$analytics_d === void 0 ? void 0 : (_window11$analytics_d2 = _window11$analytics_d.site) === null || _window11$analytics_d2 === void 0 ? void 0 : (_window11$analytics_d3 = _window11$analytics_d2.currency) === null || _window11$analytics_d3 === void 0 ? void 0 : _window11$analytics_d3.code) || ((_window12 = window) === null || _window12 === void 0 ? void 0 : (_window12$cms = _window12.cms) === null || _window12$cms === void 0 ? void 0 : (_window12$cms$site = _window12$cms.site) === null || _window12$cms$site === void 0 ? void 0 : (_window12$cms$site$cu = _window12$cms$site.currency) === null || _window12$cms$site$cu === void 0 ? void 0 : _window12$cms$site$cu.code) || '';
        },
        getSessionId: () => {
          var _window13, _window13$analytics_d, _window13$analytics_d2;
          return ((_window13 = window) === null || _window13 === void 0 ? void 0 : (_window13$analytics_d = _window13.analytics_datalayer) === null || _window13$analytics_d === void 0 ? void 0 : (_window13$analytics_d2 = _window13$analytics_d.user) === null || _window13$analytics_d2 === void 0 ? void 0 : _window13$analytics_d2.sessionId) || '';
        },
        getBrowserInfo: () => {
          var ua = navigator.userAgent,
            tem,
            M = ua.match(/(opera|chrome|safari|firefox|msie|trident(?=\/))\/?\s*(\d+)/i) || [];
          if (/trident/i.test(M[1])) {
            tem = /\brv[ :]+(\d+)/g.exec(ua) || [];
            return 'IE ' + (tem[1] || '');
          }
          if (M[1] === 'Chrome') {
            tem = ua.match(/\b(OPR|Edge?)\/(\d+)/);
            if (tem != null) return tem.slice(1).join(' ').replace('OPR', 'Opera').replace('Edg ', 'Edge ');
          }
          M = M[2] ? [M[1], M[2]] : [navigator.appName, navigator.appVersion, '-?'];
          if ((tem = ua.match(/version\/(\d+)/i)) != null) M.splice(1, 1, tem[1]);
          return M.join(' ');
        },
        identifySite: () => {
          //gets the brand and country from the URL
          let brandLookup = '';
          let countryLookup = '';
          let splitDomain = window.location.hostname.split('.');
          const brandList = /(bingo)|(highrolling)|(huone)|(kolikkopelit)|(mariacasino)|(otto(c|k)asino)|(storspelare)|(unibet)|(vlad)/;
          if (brandList.test(splitDomain[1])) {
            if (/((c|k)a(s|z)ino)|(sports)|(games)/.test(splitDomain[1])) {
              splitDomain[1] = splitDomain[1].replace(/((c|k)a(s|z)ino)|(sports)|(games)/, '');
              brandLookup = splitDomain[1];
            } else {
              brandLookup = splitDomain[1];
            }
            if (/\-/.test(brandLookup)) {
              brandLookup = brandLookup.split('-')[0];
            }
            if (/www(-(qa1|si1|pt1))?/.test(splitDomain[0])) {
              countryLookup = splitDomain[2];
              if (countryLookup === 'co') {
                countryLookup = splitDomain[3];
              } else if (countryLookup === 'com' && splitDomain[3] === 'au') {
                countryLookup = splitDomain[3];
              }
            } else {
              countryLookup = splitDomain[0];
              countryLookup = countryLookup.replace(/-(qa1|si1|pt1)/, '');
              if (/fr|nl/.test(countryLookup) && splitDomain[2] === 'be') {
                countryLookup = countryLookup + '_' + splitDomain[2];
              }
            }
            if (countryLookup === 'int') {
              countryLookup = 'com';
            }
          } else if (/hu\-(si1|qa1).32red.com/g.test(window.location.hostname)) {
            brandLookup = '32red', countryLookup = 'hu';
          } else if (/int\-(si1|qa1).32red.com/g.test(window.location.hostname)) {
            brandLookup = '32red', countryLookup = 'com';
          } else if (/www(\-((si|qa)1|prod))?\.32red\.com/g.test(window.location.hostname)) {
            brandLookup = '32red', countryLookup = 'uk';
          } else if (/www(\-((si|qa)1|prod))?\.32rosu\.ro/g.test(window.location.hostname)) {
            brandLookup = '32red', countryLookup = 'ro';
          }
          return {
            brand: brandLookup,
            country: countryLookup
          };
        },
        storageManagement: {
          NAMESPACE: 'webAnalytics',
          LOCAL_STORAGE: 'localStorage',
          SESSION_STORAGE: 'sessionStorage',
          syncValue: function setValue(name, value) {
            this._setStorage(this.LOCAL_STORAGE, name, value);
            this._setCookie(name, value, 365 * 2);
          },
          getAndSyncValue: function getValue(name) {
            let value = this._getCookie(name) || this._getStorage(this.LOCAL_STORAGE, name);
            if (typeof value !== 'undefined') this.syncValue(name, value);
            return value;
          },
          _getCookie: name => {
            // Implement your cookie retrieval logic here
          },
          _setCookie: (name, value, days) => {
            // Implement your cookie setting logic here
          },
          _isStorageAvailable: function _isStorageAvailable() {
            let isAvailable = false;
            try {
              if (typeof window !== 'undefined' && typeof window.localStorage !== 'undefined' && typeof window.sessionStorage !== 'undefined') {
                isAvailable = true;
              }
            } catch (error) {
              console.error('Error checking storage availability:', error);
            }
            return isAvailable;
          },
          _setStorage: function setStorage(storageType, name, value) {
            if (this._isStorageAvailable()) {
              const jsonData = this._getNameSpaceData(storageType);
              jsonData[name] = value;
              window[storageType].setItem(this.NAMESPACE, JSON.stringify(jsonData));
            }
          },
          _getStorage: function getStorage(storageType, name) {
            if (this._isStorageAvailable()) {
              const jsonData = this._getNameSpaceData(storageType);
              return jsonData[name];
            }
          },
          _deleteStorage: function deleteStorage(storageType, name) {
            if (this._isStorageAvailable()) {
              const jsonData = this._getNameSpaceData(storageType);
              delete jsonData[name];
              window[storageType].setItem(this.NAMESPACE, JSON.stringify(jsonData));
            }
          },
          _getNameSpaceData: function getNameSpaceData(storageType) {
            const nameSpacedData = window[storageType].getItem(this.NAMESPACE);
            return JSON.parse(nameSpacedData) || {};
          }
        },
        getSnowplowSchemaURI: schemaType => {
          //centralised schema version lookup
          const schemaVersion = {
            contest: '2-0-0',
            experiment: '1-1-1',
            experimentUserData: '1-0-0',
            casinoMyFavourites: '1-0-0',
            loadScreenInteraction: '1-0-0',
            pinFavourite: '1-0-0',
            bannerInteraction: '1-0-0',
            bannerNotification: '1-0-1',
            nextGameInteraction: '1-0-0',
            casinoGameImpressions: '1-0-0',
            splashScreenInteraction: '1-0-0',
            marketingSource: '1-0-6',
            appSettingsInteraction: '1-0-0',
            optimizationData: '1-0-0',
            cxSurvey: '2-0-0',
            casinoGameAttribute: '1-0-0',
            registrationInteraction: '2-0-1',
            casinoGame: '2-1-3',
            customInstallReferrer: '1-0-0',
            searchClickDetails: '1-0-0',
            registration: '2-0-5',
            pokerInteraction: '2-0-0',
            casinoFindingMethod: '1-1-2',
            promotion: '2-0-2',
            widget: '1-0-4',
            search: '2-1-1',
            searchFilter: '1-0-0',
            registrationComms: '1-0-0',
            login: '2-1-1',
            tournament: '1-0-5',
            gamingWidget: '1-0-0',
            messageCenterInteraction: '2-0-0',
            selfTest: '1-0-0',
            commsSelectedAtRegistration: '2-0-0',
            coupon: '2-0-1',
            mobCustomEvent: '1-0-0',
            offer: '1-0-2',
            controlsAndLimits: '1-0-3',
            error: '1-0-1',
            page: '2-0-3',
            casinoInteraction: '1-0-3',
            verification: '3-1-1',
            bonus: '1-0-2',
            popupMessage: '1-0-2',
            deposit: '1-0-1',
            bet: '2-0-1',
            device: '2-0-1',
            streamDetails: '1-1-1',
            contestInteraction: '2-0-1',
            promoOffer: '1-0-0',
            genericInteraction: '1-0-1',
            pushNotification: '1-0-0',
            customer: '1-0-1',
            depositInteraction: '1-0-1',
            game: '1-0-2',
            gameInteraction: '1-0-1',
            user: '1-0-0',
            racingContest: '1-0-0',
            racingInteraction: '1-0-0',
            racingPageInfo: '1-0-0',
            racingWidget: '1-0-0',
            cashbackInteraction: '1-0-0',
            gameNavigation: '1-0-1',
            userBalance: '1-0-0',
            paymentUserEvent: '1-0-0',
            installationInteraction: '1-0-1',
            casinoSession: '1-0-0',
            registrationSession: '3-0-0',
            betslipLineItem: '3-1-0',
            offlineInteraction: '1-0-0',
            help_centre_interaction: '2-0-0',
            notifications: '1-0-0',
            betShare: '1-0-1'
          };
          const schemaURI = `iglu:com.kindredgroup/${schemaType}/jsonschema/${schemaVersion[schemaType] || 1 - 0 - 0}`;
          return schemaURI;
        },
        getCustomerBalance: () => {
          var _window$getUserBalanc, _window14;
          let balance = ((_window$getUserBalanc = (_window14 = window).getUserBalance) === null || _window$getUserBalanc === void 0 ? void 0 : _window$getUserBalanc.call(_window14)) || {
            currencyCode: 'GBP',
            bonus: 0,
            cash: 0
          };
          let balance_value = balance.cash;
          let balance_currency = balance.currencyCode;
          let balance_bonus = balance.bonus;
          return {
            balance_value: balance_value,
            balance_currency: balance_currency,
            balance_bonus: balance_bonus
          };
        },
        getMarketingVariablesFromCookie: () => {
          // read the BSTAN paramaters from a cookie (jira ticket WARP-6522)
          const cookies = document.cookie.split(';').filter(c => c.trim().startsWith('affiliate_params='));
          let cookieValue;
          for (let i = 0; i < cookies.length; i++) {
            if (cookies[i].split('=')[1].includes('btag')) {
              cookieValue = cookies[i].split('=')[1];
            }
          }
          if (!cookieValue) {
            return null;
          }
          let parsedObject = null;
          try {
            parsedObject = JSON.parse(cookieValue);
          } catch (e) {}
          if (!parsedObject) {
            return null;
          }
          const searchString = Object.keys(parsedObject).map(key => `${encodeURIComponent(key)}=${encodeURIComponent(parsedObject[key])}`).join('&');
          return searchString.toLowerCase();
        },
        getMarketingData: () => {
          const OLD_TRACKING_CODE = analyticsHelpers.getTrackingCode();
          // URLSearchParams interface : https://developer.mozilla.org/en-US/docs/Web/API/URLSearchParams
          // URL query parameters names are lower-cased to avoid issues with capitalization
          let sanited_search = window.location.search.replace(/([^&?\/=]*)=/gi || analyticsHelpers.getCookie('queryString'), x => x.toLowerCase());
          if (sanited_search === '') sanited_search = analyticsHelpers.getMarketingVariablesFromCookie();
          const paramsObj = new URLSearchParams(sanited_search);
          const referrer = document.referrer;
          let marketingChannelId, marketingSubChannelId;
          let marketingData = {};
          const getDomainFromUrl = str => {
            if (str && str !== '') {
              const tmpUrl = new URL(str);
              return tmpUrl.hostname;
            }
          };
          const identifyChannels = (channelId, channelDomainMapping, referrer) => {
            /* identifyChannels
             ** Returns an array with [channel_id, sub_channel]
             */
            if (referrer && referrer !== '') {
              var refDomain = getDomainFromUrl(referrer);
              var currDomain = window.location.hostname;
              if (channelId === REFERRING_DOMAIN) {
                /*
                 **  Referring domain checks:
                 **  1. Referring domain present
                 **  2. Referring domain different than current domain
                 **  3. Referring domain different than the DOMAINS_REFERRING check list
                 */
                // Current referrer should not contain any of the domains in the domain mapping.
                if (currDomain !== refDomain) {
                  const res = channelDomainMapping.every(x => refDomain.indexOf(x) === -1);
                  if (res) return [channelId, refDomain];
                }
              } else {
                const res = channelDomainMapping.some(x => refDomain.indexOf(x) > -1);
                // Because unibet.co.uk contains t.co, added manual check below.
                if (res && refDomain.indexOf('unibet') === -1) return [channelId, refDomain];
              }
            }
          };
          // Check if a channel click-through was performed. Each channel has slightly different logic, especially referring domains and direct.
          // If no click-through is performed, no data is captured.
          const isChannelClickthrough = (channelParameter, referrer) => {
            // Conditions to set channel information:
            // 1. ch exists on the URL parameters
            // 2. ch does not exist but referring domain exists within any of the domains mapping
            // 3. ch does not exist, referring domain does not exist and it is start of visit -> Direct visit.
            const _helpers = analyticsHelpers;
            // mark as we need to find a way without using tealium to get the first page view of the session
            const pageCount = localStorage.getItem('pageCount');
            let sessionHitNumber = parseInt(pageCount);
            if (channelParameter && channelParameter !== '') {
              return true;
            } else if (_helpers.getTrackingCode() !== '') {
              return false;
            } else if (referrer && referrer !== '') {
              // Referrer needs to match any of the domain mappings
              if (identifyChannels(NATURAL_SEARCH, DOMAINS_NATURAL_SEARCH, referrer) || identifyChannels(NATURAL_SOCIAL, DOMAINS_NATURAL_SOCIAL, referrer) || identifyChannels(REFERRING_DOMAIN, DOMAINS_REFERRING, referrer)) return true;
            } else if (sessionHitNumber === 1 && referrer === '') return true;else return false;
          };
          const IS_CHANNEL_CTR = isChannelClickthrough(paramsObj.get('ch'), referrer);
          const helpIdentifyNaturalChannels = referrer => {
            // Natural search, Natural Social and Referring domains do not have ch and sub_ch parameters.
            const naturalSearchInfo = identifyChannels(NATURAL_SEARCH, DOMAINS_NATURAL_SEARCH, referrer);
            const natural_social_info = identifyChannels(NATURAL_SOCIAL, DOMAINS_NATURAL_SOCIAL, referrer);
            const referring_info = identifyChannels(REFERRING_DOMAIN, DOMAINS_REFERRING, referrer);
            if (naturalSearchInfo) {
              marketingChannelId = naturalSearchInfo[0];
              marketingSubChannelId = naturalSearchInfo[1];
            } else if (natural_social_info) {
              marketingChannelId = natural_social_info[0];
              marketingSubChannelId = natural_social_info[1];
            } else if (referring_info) {
              marketingChannelId = referring_info[0];
              marketingSubChannelId = referring_info[1];
            }
            return {
              marketingChannelId,
              marketingSubChannelId
            };
          };
          if (IS_CHANNEL_CTR) {
            if (paramsObj.has('ch')) {
              marketingChannelId = paramsObj.get('ch');
              if (paramsObj.get('ch') === AFFILIATE) {
                // Affiliate custom sub_channel
                const tmpBtag = paramsObj.get('btag');
                if (tmpBtag) marketingSubChannelId = tmpBtag.split('_')[0];
              } else if (paramsObj.get('ch') === SATELLITE_SITE) {
                // satellite sites sub_channel -> referring domain
                marketingSubChannelId = getDomainFromUrl(referrer);
              } else if (paramsObj.has('sub_ch')) marketingSubChannelId = paramsObj.get('sub_ch');else if (paramsObj.has('subch')) marketingSubChannelId = paramsObj.get('subch');
            } else {
              ({
                marketingChannelId,
                marketingSubChannelId
              } = helpIdentifyNaturalChannels(referrer));
            }
          } else if (OLD_TRACKING_CODE !== '') {
            if (/^44/i.test(OLD_TRACKING_CODE)) {
              marketingChannelId = 'paid_search';
            } else if (/^52/i.test(OLD_TRACKING_CODE)) {
              marketingChannelId = 'paid_social';
            } else if (/^49/i.test(OLD_TRACKING_CODE)) {
              marketingChannelId = 'display';
            } else if (/^popunder:/i.test(OLD_TRACKING_CODE)) {
              marketingChannelId = 'popunder';
            } else if (/^1/i.test(OLD_TRACKING_CODE)) {
              marketingChannelId = AFFILIATE;
              // Affiliate custom sub_channel
              var tmpBtag = paramsObj.get('btag');
              if (tmpBtag) marketingSubChannelId = tmpBtag.split('_')[0];
              var popunderIds = ['81764725', '81763824', '81763501', '81763091', '81750246', '81750186', '81750185', '81750179', '81749212', '81748885', '81748470', '81748371', '81746924', '81745741', '81744888', '81744811', '81744284', '81742790', '81742196', '6006407', '6005908', '6005292', '6005291', '6005264', '6005195', '320667814', '320667735', '320667448', '320667438', '320666043', '320665405', '127656443', '127656177', '127655244', '127654917', '127654816', '127654173', '81745104', '81747181', '81747374', '81747494', '81749955', '81763812', '320667825', '320667826', '320668861', '320669226', '320669583', '320669908'];
              var splitTrackingCode = OLD_TRACKING_CODE.split(':');
              if (popunderIds.indexOf(splitTrackingCode[1]) > -1) {
                marketingChannelId = 'popunder';
              }
            } else if (/^(email|46:|57:)/i.test(OLD_TRACKING_CODE)) {
              marketingChannelId = 'email';
            } else if (/^55/i.test(OLD_TRACKING_CODE)) {
              marketingChannelId = 'mobile_ads';
            } else if (/^50/i.test(OLD_TRACKING_CODE)) {
              marketingChannelId = 'satellite_site';
            } else if (/^PNF/i.test(OLD_TRACKING_CODE)) {
              marketingChannelId = 'push';
            } else {
              ({
                marketingChannelId,
                marketingSubChannelId
              } = helpIdentifyNaturalChannels(referrer));
            }
            marketingSubChannelId = OLD_TRACKING_CODE || '';
          }
          // All parameters are being captued from the URL
          marketingData.marketing_channel_id = marketingChannelId || '';
          marketingData.marketing_sub_channel_id = marketingSubChannelId || '';
          /* Set tracking code equal to subchannel if the channel is :
           *   Paid Search
           *   Paid Social
           *   Display
           *   Email
           *   Dedicated Mobile Ads
           *   Satellite sites
           */
          if (/^paid_(search|social)|display|email|mobile_ads|satellite_site$/.test(marketingChannelId)) {
            marketingData.campaign_tracking_code = marketingSubChannelId;
          }
          marketingData.marketing_kindred_placement_id = paramsObj.get('kpid') || '';
          marketingData.marketing_keyword = paramsObj.get('keyword') || '';
          marketingData.marketing_campaign_id = paramsObj.get('k_cid') || paramsObj.get('campaignId') || paramsObj.get('campaignid') || '';
          if (marketingData.marketing_channel_id === 'email' && (marketingData.marketing_campaign_id === '' || marketingData.marketing_campaign_id == 'notset')) {
            marketingData.marketing_campaign_id = paramsObj.get('templateid') || 'notset';
          }
          marketingData.marketing_btag = paramsObj.get('btag') || '';
          marketingData.marketing_nf_pid = paramsObj.get('pid') || '';
          marketingData.marketing_nf_bid = paramsObj.get('bid') || '';
          marketingData.marketing_network_id = paramsObj.get('affiliateid') || '';
          marketingData.marketing_ad_id = paramsObj.get('adid') || '';
          marketingData.marketing_product_info = paramsObj.get('productid') || '';
          marketingData.marketing_cct_tracking_id = paramsObj.get('trackingid') || '';
          if (paramsObj.get('trackingid2') !== null && (marketingData.marketing_cct_tracking_id === '' || marketingData.marketing_cct_tracking_id == 'notset')) {
            marketingData.marketing_cct_tracking_id = paramsObj.get('trackingid2') || '';
          }
          marketingData.marketing_cct_group_id = paramsObj.get('k_gid') || '';
          marketingData.marketing_recruiter_id = paramsObj.get('recruiterid') || '';
          marketingData.marketing_timestamp = Math.floor(Date.now() / 1000);
          marketingData.marketing_gamename = paramsObj.get('gamename') || '';
          marketingData.marketing_acquisition_offer_id = paramsObj.get('acquisitionofferid') || '';
          if (marketingData.marketing_channel_id !== '') {
            analyticsHelpers.setCookie('queryParameters', sanited_search, '');
          }
          if (paramsObj.get('page_referrer')) {
            snowplow('setReferrerUrl', paramsObj.get('page_referrer'));
          }
          return marketingData;
        },
        getMarketingDataUpdated: () => {
          //initialise marketing data object
          let marketingData = {};
          /*
          the below function is the main function for marketingData
          it calls relevant functions below based on the query string type and/or channel (in the case of natural channels)
          */
          function structureMarketingData() {
            /*
            get query string from query parameters or queryString cookie 
            -the cookie is set on welcome pages and has two purposes:
            --the query string does not persist to the main sites, so we can still capture the query string
            --prevents us missing query string from private windows or ad-blockers as these can prevent GTM firing
            */
            let trackingCode = window.location.search;
            if (analyticsHelpers.getCookie('queryString')) {
              trackingCode = analyticsHelpers.getCookie('queryString');
              analyticsHelpers.deleteCookie('queryString');
            }
            // Only lower-case the keys, not the values
            let paramsObject = {};
            for (let [key, value] of new URLSearchParams(trackingCode)) {
              paramsObject[key.toLowerCase()] = value;
            }
            //declare referrer
            let referrer = document.referrer;

            //popunder check and configure
            let isPopunder = false;
            if (referrer.indexOf('/pop/') > -1) {
              isPopunder = true;
              if (paramsObject.mktid) {
                paramsObject.mktid = paramsObject.mktid.replace('1:', 'popunder:');
              }
              if (paramsObject.cid) {
                paramsObject.cid = paramsObject.cid.replace('1:', 'popunder:');
              }
            }
            //paid channel check
            if (paramsObject && paramsObject !== '' && paramsObject !== null) {
              //bstan check
              if ('ch' in paramsObject) {
                marketingData = bstan(paramsObject);
              }
              //stan check
              else if (isPopunder || 'mktid' in paramsObject || 'cid' in paramsObject) {
                marketingData = stan(paramsObject);
              } else if ('utm_medium' in paramsObject) {
                marketingData.channel = paramsObject.utm_medium;
                const medium = paramsObject.utm_medium;
                const source = paramsObject.utm_source || 'NONE';
                const content = paramsObject.utm_content || 'NONE';
                const campaign = paramsObject.utm_campaign || 'NONE';
                const term = paramsObject.utm_term || 'NONE';
                marketingData.sub_channel = medium + ':' + source + ':' + content + ':' + campaign + ':' + term;
              }
            }
            //natural channel check
            else if (!paramsObject && referrer && referrer !== '') {
              let naturalChannel = naturalChannelHandler(referrer);
              if (naturalChannel === ('search' )) {
                naturalChannel = 'natural_' + naturalChannel;
              } else if (naturalChannel !== ('banking' )) {
                naturalChannel = 'referring_domain';
              }
              marketingData.channel = naturalChannel;
              marketingData.sub_channel = referrer;
            }

            /*
            set Snowplow referrer for internal redirects, 
            this is for friendly pagepaths, they're shortened in SERPs but instantly redirect so the referrer needs to be set as query param
            */
            if (paramsObject.page_referrer && paramsObject.page_referrer !== '') {
              snowplow('setReferrerUrl', paramsObject.get('page_referrer'));
            }
            //returns marketing data to getMarketingDataUpdated function
            return marketingData;
          }

          //handling for bstan (beyond STAN) parameters, these should be in use across most channels
          function bstan(paramsObject) {
            let sub_ch = paramsObject.sub_ch;
            if (paramsObject.ch === 'affiliate' && paramsObject !== null && paramsObject !== void 0 && paramsObject.btag) {
              sub_ch = paramsObject === null || paramsObject === void 0 ? void 0 : paramsObject.btag.split('_')[0];
            }
            marketingData.channel = paramsObject.ch;
            marketingData.sub_channel = sub_ch;
            marketingData.kindred_placement_id = paramsObject.kpid || '';
            marketingData.ad_id = paramsObject.adid || '';
            marketingData.btag = paramsObject.btag || '';
            marketingData.campaign_id = paramsObject.k_cid || paramsObject.campaignid || '';
            marketingData.cct_group_id = paramsObject.k_gid || '';
            marketingData.cct_tracking_id = paramsObject.trackingid || '';
            marketingData.recruiter_id = paramsObject.recruiterid || '';
            marketingData.gamename = paramsObject.gamename || '';
            marketingData.acquisition_offer_id = paramsObject.acquisition_offer_id || '';
            marketingData.keyword = paramsObject.keyword || '';
            marketingData.nf_pid = paramsObject.pid || '';
            marketingData.nf_bid = paramsObject.bid || '';
            marketingData.network_id = paramsObject.affiliateid || '';
            marketingData.product_id = paramsObject.productid || '';
            //returns marketing data to the structureMarketingData function
            return marketingData;
          }

          //handling for stan (legacy) parameters, these are being phased out but we still receive some traffic using these
          function stan(paramsObject) {
            let mktid = paramsObject.mktid.split(':');
            let channelIds = {
              1: 'affiliate',
              44: 'paid_search',
              46: 'email',
              49: 'display',
              50: 'satellite_site',
              52: 'paid_social',
              55: 'mobile_ads',
              57: 'email',
              popunder: 'popunder',
              email: 'email',
              PNF: 'push'
            };
            if (channelIds[mktid[0]]) {
              marketingData.channel = channelIds[mktid[0]];
            }
            let popunderIds = ['81764725', '81763824', '81763501', '81763091', '81750246', '81750186', '81750185', '81750179', '81749212', '81748885', '81748470', '81748371', '81746924', '81745741', '81744888', '81744811', '81744284', '81742790', '81742196', '6006407', '6005908', '6005292', '6005291', '6005264', '6005195', '320667814', '320667735', '320667448', '320667438', '320666043', '320665405', '127656443', '127656177', '127655244', '127654917', '127654816', '127654173', '81745104', '81747181', '81747374', '81747494', '81749955', '81763812', '320667825', '320667826', '320668861', '320669226', '320669583', '320669908'];
            if (popunderIds.indexOf(mktid[1]) > -1) {
              marketingData.channel = 'popunder';
            }
            //returns marketing data to the structureMarketingData function
            return marketingData;
          }

          /*
          natural channel identification; these channels don't typically have query strings so are identified from the referrer
          */
          function naturalChannelHandler(referrer) {
            let naturalChannels = {
              search: ['www.google.', 'bing.', 'search.yahoo.', 'search.seznam.', '.yandex.', '.ask.'],
              social: ['facebook.com', 't.co', 'pinterest.', 'linked.com', 'plus.google', 'instagram.com', 'hootsuite.com'],
              internal: ['.unibet.', '.unibetcasino.', '.unibetgames.', '.unibetsports.', '.bingo.', '.vladcazino.', '.highroller.', '.highrolling.', '.storspelare.', '.storspiller.', '.igame.', '.casinohuone.', '.kolikkopelit.', '.mariacasino.', 'paypal.com', 'merchant.itsme', '.32red.', '.32rosu.', '.ottokasino', '.ottocasino.'],
              banking: ['diensten.snsbank.nl', '.abnamro.nl', 'diensten.asnbank.nl', 'idin.bunq.com', 'ideal.ing.nl', 'idp.rabobank.nl', 'diensten.regiobank.nl', 'diensten.snsbank.nl', 'unibet.criipto.id', 'unibet.mitid.dk']
            };
            for (const [channel, patterns] of Object.entries(naturalChannels)) {
              if (patterns.some(pattern => referrer.includes(pattern))) {
                //returns the channel to the structureMarketingData function
                return channel;
              }
            }
            return null;
          }
          //calls the main marketingData handling function
          structureMarketingData();
          //returns marketing data to whichever function called getMarketingDataUpdated
          return marketingData;
        },
        getMarketingConsent: () => {
          let OneTrustConsent = analyticsHelpers.getCookie('OptanonConsent');
          let marketingConsent = false;
          if (OneTrustConsent) {
            if (OneTrustConsent.indexOf('C0004%3A1') > -1 || OneTrustConsent.indexOf('C0004:1') > -1) {
              marketingConsent = true;
            }
          }
          return marketingConsent;
        },
        waitForElm: selector => {
          return new Promise(resolve => {
            if (document.querySelector(selector)) {
              return resolve(document.querySelector(selector));
            }
            const observer = new MutationObserver(mutations => {
              if (document.querySelector(selector)) {
                resolve(document.querySelector(selector));
                observer.disconnect();
              }
            });
            observer.observe(document.body, {
              childList: true,
              subtree: true
            });
          });
        },
        belgiumClientId: () => {
          var clientId_cookie = analyticsHelpers.storageManagement._getCookie('clientId') || '';
          if (clientId_cookie === '') {
            if (analyticsHelpers.getClientId() !== '') {
              analyticsHelpers.storageManagement._setCookie('clientId', analyticsHelpers.getClientId());
            }
          }
        },
        isPWA: () => {
          if (typeof navigator === 'undefined') return false;
          const isStandalone = window.matchMedia('(display-mode: standalone)').matches;
          return Boolean(navigator.standalone || isStandalone);
        },
        reloadCheck: () => {
          let previousPath = analyticsHelpers.storageManagement._getStorage('sessionStorage', 'previousPath');
          let pageReload = false;
          if (previousPath !== window.location.pathname) {
            analyticsHelpers.storageManagement._setStorage('sessionStorage', 'previousPath', window.location.pathname);
          } else {
            pageReload = true;
          }
          analyticsHelpers.storageManagement._setStorage('sessionStorage', 'pageReload', pageReload);
        }
      });

      //schema version lookup
      const getSnowplowSchemaURI = exports('g', schemaType => {
        //centralised schema version lookup
        const schemaVersion = {
          contest: '2-0-0',
          experiment: '1-1-1',
          experimentUserData: '1-0-0',
          casinoMyFavourites: '1-0-0',
          loadScreenInteraction: '1-0-0',
          pinFavourite: '1-0-0',
          bannerInteraction: '1-0-0',
          bannerNotification: '1-0-1',
          nextGameInteraction: '1-0-0',
          casinoGameImpressions: '1-0-0',
          splashScreenInteraction: '1-0-0',
          marketingSource: '1-0-6',
          appSettingsInteraction: '1-0-0',
          optimizationData: '1-0-0',
          cxSurvey: '2-0-0',
          casinoGameAttribute: '1-0-0',
          registrationInteraction: '2-0-1',
          casinoGame: '2-1-3',
          customInstallReferrer: '1-0-0',
          searchClickDetails: '1-0-0',
          registration: '2-0-5',
          pokerInteraction: '2-0-0',
          casinoFindingMethod: '1-1-2',
          promotion: '2-0-2',
          widget: '1-0-6',
          search: '2-1-1',
          searchFilter: '1-0-0',
          registrationComms: '1-0-0',
          login: '2-1-1',
          tournament: '1-0-5',
          gamingWidget: '1-0-0',
          messageCenterInteraction: '2-0-0',
          selfTest: '1-0-0',
          commsSelectedAtRegistration: '2-0-0',
          coupon: '2-0-1',
          mobCustomEvent: '1-0-0',
          offer: '1-0-2',
          controlsAndLimits: '1-0-3',
          error: '1-0-1',
          page: '2-0-3',
          casinoInteraction: '1-0-3',
          verification: '3-1-1',
          bonus: '1-0-2',
          popupMessage: '1-0-2',
          deposit: '1-0-1',
          bet: '2-0-1',
          device: '2-0-1',
          streamDetails: '1-1-1',
          contestInteraction: '2-0-1',
          promoOffer: '1-0-0',
          genericInteraction: '1-0-1',
          pushNotification: '1-0-0',
          customer: '1-0-1',
          depositInteraction: '1-0-1',
          game: '1-0-2',
          gameInteraction: '1-0-1',
          user: '1-0-0',
          racingContest: '1-0-0',
          racingInteraction: '1-0-0',
          racingPageInfo: '1-0-0',
          racingWidget: '1-0-0',
          cashbackInteraction: '1-0-0',
          gameNavigation: '1-0-1',
          userBalance: '1-0-0',
          paymentUserEvent: '1-0-0',
          installationInteraction: '1-0-1',
          casinoSession: '1-0-0',
          registrationSession: '3-0-0',
          betslipLineItem: '3-1-0',
          offlineInteraction: '1-0-0',
          help_centre_interaction: '2-0-0',
          notifications: '1-0-0',
          betShare: '1-0-2',
          postLoginInteraction: '4-0-2'
        };
        const schemaURI = `iglu:com.kindredgroup/${schemaType}/jsonschema/${schemaVersion[schemaType] || '1-0-0'}`;
        return schemaURI;
      });

      //update global contexts, specify which contexts to update
      const updateSnowplowGlobalContexts = exports('h', function () {
        let data = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : {};
        if (!window.snowplow) {
          initSnowplow();
        }
        const {
          applicationId,
          brand,
          clientId,
          currency,
          deviceGroup,
          jurisdiction,
          locale,
          channel,
          isApp,
          isLoggedIn,
          preferredCurrency,
          market,
          isKwp,
          oddsFormat
        } = useDataLayer();
        const customerId = getCustomerId(data);
        //webview js does not support add/removeGlobalContexts. Global contexts for webviews are setup in native part of the app
        if (isApp) {
          return;
        }
        const getSnowplowUserBalanceSchema = () => {
          const balance = analyticsHelpers.getCustomerBalance();
          return {
            schema: getSnowplowSchemaURI('userBalance'),
            data: {
              value: balance.balance_value,
              currency: balance.balance_currency,
              bonus: balance.balance_bonus
            }
          };
        };
        const pageSchema = {
          schema: getSnowplowSchemaURI('page'),
          data: {
            brand: brand,
            market: market,
            channel: channel,
            jurisdiction: jurisdiction,
            oddsFormat: oddsFormat,
            countryCode: locale,
            shortCode: locale.split('_')[0],
            timeZone: '',
            playForFunRequiresLogin: false,
            currencyCode: currency
          }
        };
        const deviceSchema = {
          schema: getSnowplowSchemaURI('device'),
          data: {
            type: deviceGroup,
            os: '',
            osVersion: '',
            applicationId: 'kwp',
            isApp: isApp,
            appVersion: analyticsHelpers.getAppVersion()
          }
        };
        const customerSchema = {
          schema: getSnowplowSchemaURI('customer'),
          data: {
            id: customerId || 0,
            sessionId: '',
            isLoggedIn: isLoggedIn
          }
        };
        const balanceSchema = getSnowplowUserBalanceSchema();

        // Remove existing contexts first
        window.snowplow('removeGlobalContexts', [pageSchema, deviceSchema, customerSchema, balanceSchema]);

        // Add updated contexts
        window.snowplow('addGlobalContexts', [pageSchema, deviceSchema, customerSchema, balanceSchema]);
      });

      //general snowplow event firing
      const fireSnowplowEvent = exports('f', function (schema_to_send) {
        let data = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : {};
        if (schema_to_send) {
          updateSnowplowGlobalContexts(data);
          window.snowplow('trackSelfDescribingEvent', schema_to_send);
          if (analyticsHelpers.shouldLog()) {
            console.log("ADC: '" + schema_to_send.event.data.type + "' to '" + schema_to_send.event.schema + "'");
          }
          try {
            if (analyticsHelpers.storageManagement._getStorage("sessionStorage", "analytics-dev-event")) {
              analyticsHelpers.storageManagement._setStorage("sessionStorage", "analytics-dev-app-event", schema_to_send);
              // Notify dev tools (analytics-trigger-events App tab) and optional journey tracker — same payload as sessionStorage
              document.dispatchEvent(new CustomEvent('analytics-dev-tracker-event', {
                detail: schema_to_send
              }));
            } else {
              analyticsHelpers.storageManagement._deleteStorage("sessionStorage", "analytics-dev-app-event");
            }
          } catch (error) {
            console.log("ADC: Dev tools storage failed...Schema to send:", schema_to_send);
          }
        }
      });

      function pageViewContext() {
        //marketing source context
        const {
          getMarketingDataUpdated,
          getMarketingData
        } = marketingData();
        const {
          market
        } = useDataLayer();
        let PVcontexts = {
          context: []
        };
        let mkData;
        try {
          mkData = getMarketingDataUpdated();
          if (!mkData.channel) {
            mkData = getMarketingData();
          }
        } catch (e) {
          mkData = getMarketingData();
        }
        if (mkData.marketing_channel_id || mkData.channel) {
          PVcontexts.context.push({
            schema: getSnowplowSchemaURI("marketingSource"),
            data: {
              "channel": mkData.channel || mkData.marketing_channel_id,
              "subChannel": mkData.sub_channel || mkData.marketing_sub_channel_id,
              "kindredPlacementId": mkData.kindred_placement_id || mkData.marketing_kindred_placement_id || "",
              "keyword": mkData.keyword || mkData.marketing_keyword || null,
              "campaignId": mkData.campaign_id || mkData.marketing_campaign_id || null,
              "btag": mkData.btag || mkData.marketing_btag || null,
              "nfPid": mkData.nf_pid || mkData.marketing_nf_pid || null,
              "nfBid": mkData.nf_bid || mkData.marketing_nf_bid || null,
              "networkId": mkData.network_id || mkData.marketing_network_id || null,
              "adId": mkData.ad_id || mkData.marketing_ad_id || null,
              "productInfoId": mkData.product_id || mkData.marketing_product_info || "",
              "cctTrackingId": mkData.cct_tracking_id || mkData.marketing_cct_tracking_id || null,
              "cctGroupId": mkData.cct_group_id || mkData.marketing_cct_group_id || null,
              "recruiterId": mkData.recruiter_id || mkData.marketing_recruiter_id || null,
              "gamename": mkData.gamename || mkData.marketing_gamename || null,
              "acquisitionOfferId": mkData.acquisition_offer_id || mkData.marketing_acquisition_offer_id || null
            }
          });
        }

        /* ---- additional contexts ---- */
        //SE registration CTA experiment
        if (market === 'se' && window.location.pathname === '/registration') {
          PVcontexts.context.push({
            schema: getSnowplowSchemaURI("login"),
            "data": {
              "type": "appeared",
              "method": null,
              "ctaClicked": null,
              "widget_name": "BankId Login Page",
              "is_first_login": false,
              "marketingConsent": null
            }
          });
        }
        //Topnav product clicked
        if (analyticsHelpers.storageManagement._getStorage("sessionStorage", "topNav")) {
          PVcontexts.context.push(analyticsHelpers.storageManagement._getStorage("sessionStorage", "topNav"));
          analyticsHelpers.storageManagement._deleteStorage("sessionStorage", "topNav");
        }
        return PVcontexts;
      }

      //pages with pageView event
      function firePageview(data) {
        let attempt = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : 1;
        const {
          isApp
        } = useDataLayer();
        if (window.snowplow) {
          const pageAccessedByReload = window.performance.getEntriesByType('navigation').map(nav => nav.type).includes('reload');
          if (pageAccessedByReload && !isApp) {
            snowplow('setReferrerUrl', window.location.href);
          }
          const count = sessionStorage.getItem('pageCount');
          if (!count) {
            sessionStorage.setItem('pageCount', 1);
          } else {
            sessionStorage.setItem('pageCount', parseInt(count) + 1);
          }
          updateSnowplowGlobalContexts();
          if (!isApp) {
            //do not fire pageView event for game navigation in casino or bingo
            if (analyticsHelpers.storageManagement._getStorage("sessionStorage", "gameNavigation") && /(live)?\-?casino|bingo/i.test(window.location.pathname)) {
              analyticsHelpers.storageManagement._deleteStorage("sessionStorage", "gameNavigation");
              return;
            } else {
              //page view for web
              window.snowplow('trackPageView', pageViewContext());
            }
          } else {
            //page view for app/webview
            window.snowplow('trackPageView');
          }
          if (window.location.pathname !== '/registration') {
            analyticsHelpers.storageManagement._deleteStorage("sessionStorage", "registrationStepsAnalytics");
          }
        } else {
          //in case window.snowplow is not available try 10 times
          if (attempt < 10) {
            setTimeout(() => firePageview(data, attempt + 1), 100);
          }
        }
      }

      function pageAccessedByReload() {
        if (window.performance.getEntriesByType('navigation').map(nav => nav.type).includes('reload')) {
          let previousPath = analyticsHelpers.storageManagement._getStorage("sessionStorage", "previousPath");
          if (window.location.pathname === previousPath) {
            return true;
          } else {
            return false;
          }
        } else {
          return false;
        }
      }
      function gameLaunchEvent(data) {
        analyticsHelpers.storageManagement._setStorage("sessionStorage", "gameOpened", true);
        let realMoneyMode = data.realMoneyMode || "";
        if (realMoneyMode == "" && typeof data.isPlayForFun !== "undefined") {
          realMoneyMode = /true/i.test(data.isPlayForFun) ? false : true;
        }
        let uniquegameId = data.uniquegameId || "";
        if (uniquegameId === "" && typeof data.gameId !== "undefined") {
          uniquegameId = data.gameId;
        }
        let currentGameName = data.gameName.replace(/:/ig, "-").toLowerCase();
        let source = data.source || "";
        let keywords = data.keywords || "";
        let gamePosition = data.launchElementPosition || "-1";
        let launchListPosition = data.launchListPosition || "-1";
        let casinoFindingMethod = "";
        let gameHref = "";
        let gameFilter = "";
        let gameOrigin = "";
        let sortingMethod = "";
        if (/^games|notifications/i.test(source)) {
          let b_source = source.split(":");
          if (gameHref == '') gameHref = location.pathname;
          if (gameFilter == '' && /^grid|provider|showMore$/i.test(b_source[1])) {
            gameFilter = b_source[2] || "";
          }
          if (gameFilter == '' && /^lastPlayed$/i.test(b_source[1])) {
            gameFilter = "last-played";
          }
          if (gameOrigin == '') gameOrigin = b_source[1] || "";
          if (/^notifications/i.test(source)) {
            gameOrigin = b_source[0] || "";
            gameFilter = b_source[1] || "";
          }
          keywords = '';
          if (/^search$/i.test(gameOrigin)) keywords = data.keywords || "no keyword";
          casinoFindingMethod = [gameFilter, currentGameName, gameHref, gamePosition, gameOrigin, keywords].join(':');
        }
        try {
          let tmp_cfm = analyticsHelpers.storageManagement._getStorage("sessionStorage", "snowplowCasinoFindMethod");
          if (tmp_cfm && casinoFindingMethod === "") {
            casinoFindingMethod = tmp_cfm.replace("{url}", location.pathname).replace("{name}", data.gameName);
            let tmpCFM = casinoFindingMethod.split(":");
            gameFilter = tmpCFM[0];
            currentGameName = tmpCFM[1];
            gameHref = tmpCFM[2];
            gamePosition = tmpCFM[3];
            gameOrigin = tmpCFM[4];
            keywords = tmpCFM[5];
            if (!pageAccessedByReload()) {
              analyticsHelpers.storageManagement._setStorage("sessionStorage", "snowplowCasinoFindMethod", "");
            }
          }
        } catch (e) {}
        if (casinoFindingMethod === "" && data.source !== "") {
          casinoFindingMethod = data.source;
        }
        if (data.sortingMethod) {
          sortingMethod = data.sortingMethod;
        }
        data.gameName || null;
        gamePosition = isNaN(gamePosition) ? -1 : parseInt(gamePosition);
        launchListPosition = isNaN(launchListPosition) ? -1 : parseInt(launchListPosition);
        let lobbyViewType = /grid|list|showMore/i.test(gameOrigin) ? gameOrigin : null;
        let container;
        if (/new\-games\-mab/i.test(data.source)) {
          container = 'new-games-mab';
        } else {
          container = /^game-widget$/i.test(data.source) ? 'game widget' : /grid|list/i.test(gameOrigin) ? 'lobby' : gameOrigin;
        }
        let casinoCategory;
        casinoCategory = analyticsHelpers.storageManagement._getStorage("sessionStorage", "casinoCategory");
        //when the user launches a game through homepage
        if (casinoCategory == null) {
          casinoCategory = 'foryou';
        }
        let pageurl = analyticsHelpers.storageManagement._getStorage("sessionStorage", "pageurl");
        if (/live-?casino/i.test(pageurl) && data.product === 'livecasino') {
          casinoCategory = 'live-casino';
        }
        analyticsHelpers.storageManagement._setStorage("sessionStorage", "casinoCategory", null);
        analyticsHelpers.storageManagement._deleteStorage("sessionStorage", "pageurl");
        if (casinoCategory) {
          gameFilter = casinoCategory;
        }
        if (/games:(grid|provider(s)?):/i.test(source)) {
          if (!container === 'new-games-mab') {
            container = source.split(":")[2].replace(/-|[0-9]{1,}/ig, " ").trim();
          }
        } else if (/games:lastPlayed/i.test(source)) {
          gameFilter = null;
          container = "last played";
        } else if (/game-banner/i.test(source)) {
          gameFilter = null;
          container = "game-banner";
        } else if (/games:tournament/i.test(source)) {
          gameFilter = null;
          container = source.replace("games:", "");
        }
        if (/direct/i.test(casinoFindingMethod)) {
          container = gameFilter = "";
        }
        if (gamePosition > 1000) {
          gamePosition = 1000;
        }
        if (launchListPosition > 1000) {
          launchListPosition = 1000;
        }
        if (sortingMethod === "popular") {
          container = 'new-games-mab';
        }
        if (container === 'new-games-mab') {
          gameFilter = container;
        }
        analyticsHelpers.storageManagement._setStorage("sessionStorage", "snowplowCasinoFindMethod", casinoFindingMethod);
        analyticsHelpers.storageManagement._setStorage("sessionStorage", "snowplowCasinoLaunchSource", data.source);
        if (pageAccessedByReload()) {
          //if(!/reload\:/i.test(analyticsHelpers.storageManagement._getStorage("sessionStorage","snowplowCasinoLaunchSource"))&&!/reload\:/i.test(analyticsHelpers.storageManagement._getStorage("sessionStorage","snowplowCasinoFindMethod"))){
          if (!/reload\:/i.test(analyticsHelpers.storageManagement._getStorage("sessionStorage", "snowplowCasinoLaunchSource")) && analyticsHelpers.storageManagement._getStorage("sessionStorage", "snowplowCasinoLaunchSource") === 'direct' && !/reload\:/i.test(analyticsHelpers.storageManagement._getStorage("sessionStorage", "snowplowCasinoFindMethod"))) {
            data.source = "reload: " + analyticsHelpers.storageManagement._getStorage("sessionStorage", "snowplowCasinoLaunchSource");
            casinoFindingMethod = "reload: " + analyticsHelpers.storageManagement._getStorage("sessionStorage", "snowplowCasinoFindMethod");
            gameFilter = casinoCategory;
          } else {
            data.source = analyticsHelpers.storageManagement._getStorage("sessionStorage", "snowplowCasinoLaunchSource");
            casinoFindingMethod = analyticsHelpers.storageManagement._getStorage("sessionStorage", "snowplowCasinoFindMethod");
            gameFilter = casinoCategory;
          }
        }
        if (data.source === 'direct') {
          let previousPath = analyticsHelpers.storageManagement._getStorage("sessionStorage", "previousPath");
          if (/promotions/g.test(previousPath)) {
            data.source = "Promotions Page";
          } else if (/bonus/g.test(previousPath)) {
            data.source = "Bonus Page";
          }
        }
        let schema_to_send = {
          event: {
            schema: getSnowplowSchemaURI("casinoInteraction"),
            data: {
              type: "launch"
            }
          },
          context: [{
            schema: getSnowplowSchemaURI("casinoGame"),
            data: {
              "id": uniquegameId,
              "name": data.gameName,
              "launchSource": data.source || "",
              "isPlayForFun": !realMoneyMode,
              "isPlayForMoney": realMoneyMode,
              "launchPosition": gamePosition,
              "launchListPosition": launchListPosition,
              "findingMethod": casinoFindingMethod,
              "launchPage": data.referrerPathname
            }
          }, {
            schema: getSnowplowSchemaURI("casinoFindingMethod"),
            data: {
              "casinoGameId": uniquegameId,
              "category": gameFilter,
              "container": container,
              "position": gamePosition,
              "searchKeyword": keywords,
              "lobbyViewType": lobbyViewType,
              "sortingMethod": sortingMethod
            }
          }]
        };
        if (data.selectedFilters !== undefined) {
          let filters_schema = [];
          for (let filterType in data.selectedFilters) {
            let filterValues = data.selectedFilters[filterType];
            filterValues.forEach(filterValue => {
              switch (filterType) {
                case "subVendorName":
                  filterType = "provider";
                  break;
                case "mainFeature":
                  filterType = "feature";
                  break;
                case "mainTheme":
                  filterType = "theme";
                  break;
                default:
                  filterType = filterType;
                  break;
              }
              filters_schema.push({
                schema: getSnowplowSchemaURI("searchFilter"),
                data: {
                  "type": filterType,
                  "value": filterValue
                }
              });
            });
          }
          schema_to_send.context = schema_to_send.context.concat(filters_schema);
        }
        fireSnowplowEvent(schema_to_send);
      }
      function gameMenuInteraction(data) {
        let schema_to_send = {
          event: {
            schema: getSnowplowSchemaURI("casinoInteraction"),
            data: {
              type: "",
              menuName: ""
            }
          }
        };
        schema_to_send.event.data = {};
        if (data.type === "jackpot all games") {
          let menuName = data.source + "_" + data.container + "_" + data.action;
          schema_to_send.event.data.type = data.type;
          schema_to_send.event.data.menuName = menuName;
        } else {
          schema_to_send.event.data.type = "menu interaction";
          schema_to_send.event.data.menuName = data.label;
        }
        if (data.label === "close_game") {
          closeGame('menu interaction', schema_to_send);
        }
        fireSnowplowEvent(schema_to_send);
      }
      function closeGame(close_method, schema_to_send) {
        if (!pageAccessedByReload()) {
          analyticsHelpers.storageManagement._deleteStorage("sessionStorage", "snowplowCasinoFindMethod");
          analyticsHelpers.storageManagement._deleteStorage("sessionStorage", "snowplowCasinoLaunchSource");
        }
        analyticsHelpers.storageManagement._setStorage("sessionStorage", "gameOpened", false);
        if (close_method === 'navigation') {
          fireSnowplowEvent(schema_to_send);
        }
      }
      function nextGameInteraction(data) {
        let schema_to_send = {
          event: {
            schema: getSnowplowSchemaURI("nextGameInteraction"),
            data: {
              "type": data.type,
              "container": data.container,
              "casinoGameId": data.casinoGameId,
              "position": data.position
            }
          }
        };
        closeGame('next game', schema_to_send);
        fireSnowplowEvent(schema_to_send);
      }

      var casinoInGameInteractions = /*#__PURE__*/Object.freeze({
        __proto__: null,
        closeGame: closeGame,
        gameLaunchEvent: gameLaunchEvent,
        gameMenuInteraction: gameMenuInteraction,
        nextGameInteraction: nextGameInteraction
      });

      function gamingWidgetInteraction(data) {
        if (!/load/i.test(data.action)) {
          //let data = e.detail;
          let schema_to_send = {
            event: {
              schema: getSnowplowSchemaURI("gamingWidget"),
              data: {
                "action": data.action,
                "userViewCount": data.userViewCount,
                "ctaClicked": data.ctaClicked,
                "container": data.container || null,
                "widgetType": data.widgetType || null
              }
            }
          };
          if (data.widgetType == "game") {
            schema_to_send.context = [{
              schema: getSnowplowSchemaURI("casinoGame"),
              data: {
                "id": data.widgetDetails.id,
                "name": data.widgetDetails.name,
                "launchSource": "",
                "isPlayForFun": false,
                "isPlayForMoney": true,
                "launchPosition": 0,
                "findingMethod": null
              }
            }];
            if (/click/i.test(data.action)) {
              try {
                analyticsHelpers.storageManagement._setStorage("sessionStorage", "snowplowCasinoFindMethod", "widget:" + name + ":{url}::" + data.container);
              } catch (e) {}
            }
          } else if (data.widgetType == "tournament") {
            schema_to_send.context = [{
              schema: getSnowplowSchemaURI("tournament"),
              data: {
                "type": "widget " + data.action,
                "id": data.widgetDetails.id,
                "name": data.widgetDetails.name,
                "startTime": null,
                "endTime": null,
                "status": data.widgetDetails.status.toLowerCase(),
                "gameIds": data.gamesIdsInTournament || null,
                "gameNames": data.gamesNamesInTournament || null,
                "location": data.container,
                "elementPosition": data.elementPosition || null,
                "tournamentPosition": data.tournamentPosition || null,
                "productType": data.widgetDetails.productType
              }
            }];
          }
          fireSnowplowEvent(schema_to_send);
        }
      }
      function gameNavigation(data) {
        let action = data.action.toLowerCase();
        let schema_to_send = {
          event: {
            schema: getSnowplowSchemaURI("gameNavigation"),
            data: {
              "action": action,
              "name": data.navigation_id,
              "section": data.section || null,
              "position": data.position || null
            }
          }
        };
        try {
          analyticsHelpers.storageManagement._setStorage("sessionStorage", "casinoCategory", data.navigation_id);
        } catch (e) {}
        if (action === "click") {
          try {
            //set storage to supress regular pageViews
            analyticsHelpers.storageManagement._setStorage("sessionStorage", "gameNavigation", true);
          } catch (e) {}
          let pgContexts = pageViewContext().context.concat(schema_to_send.event);
          window.snowplow('trackPageView', {
            context: pgContexts
          });
        } else {
          // Just fire the event immediately for other actions
          fireSnowplowEvent(schema_to_send);
        }
      }
      function setDefaultCategoryFilter() {
        analyticsHelpers.waitForElm("[data-test-name*='game-category-navigation'] a").then(e => {
          let defaultCat = null;
          let currentpathnameparts = location.href.split("/");
          if (/(www|hu)(-(qa1|si1|pt1|prod))?.32red(-\d+)?\.com/i.test(window.location.hostname)) {
            defaultCat = currentpathnameparts[currentpathnameparts.length - 1].split("?")[0];
          } else {
            defaultCat = currentpathnameparts[currentpathnameparts.length - 1];
          }
          let categoriesIcons = document.querySelectorAll("[data-test-name*='game-category-navigation'] a");
          if (/(live-?)?casino|bingo|softgames/i.test(defaultCat)) {
            let tmppathparts = categoriesIcons[0].href.split("/");
            defaultCat = tmppathparts[tmppathparts.length - 1];
          }
          analyticsHelpers.storageManagement._setStorage("sessionStorage", "casinoCategory", defaultCat || null);
        });
      }
      function gameSearchModule(data) {
        let product = "casino";
        let type = "start";
        if (/searchNoResults/i.test(data.searchStatus)) type = "fail";
        if (/searchSuccess/i.test(data.searchStatus)) type = "success";
        let keyword = data.searchTerm || "";
        let numberOfResults = data.numOfReturnedGames || 0;
        let schema_to_send = {
          event: {
            schema: getSnowplowSchemaURI("search"),
            data: {
              "type": type,
              "product": product,
              "keyword": keyword,
              "numberOfResults": numberOfResults,
              "topResults": data.topFiveResults || null
            }
          }
        };
        if (typeof data.filters !== "undefined" && data.filters.length > 0) {
          schema_to_send.context = schema_to_send.context || [];
          data.filters.forEach(filter => {
            switch (filter.type) {
              case "subVendorName":
                filter.type = "provider";
                break;
              case "mainFeature":
                filter.type = "feature";
                break;
              case "mainTheme":
                filter.type = "theme";
                break;
              default:
                filter.type = filter.type;
                break;
            }
            schema_to_send.context.push({
              schema: getSnowplowSchemaURI("searchFilter"),
              data: {
                "type": filter.type || "not available",
                "value": filter.value.attributeValue || "not available"
              }
            });
          });
        }
        fireSnowplowEvent(schema_to_send);
      }

      var casinoLobbyInteractions = /*#__PURE__*/Object.freeze({
        __proto__: null,
        gameNavigation: gameNavigation,
        gameSearchModule: gameSearchModule,
        gamingWidgetInteraction: gamingWidgetInteraction,
        setDefaultCategoryFilter: setDefaultCategoryFilter
      });

      class UniversalAnalyticsSender {
        send(eventType, data) {
          try {
            console.log(`Sending event: ${eventType} with data:`, data);
          } catch (error) {
            console.error(error);
          }
        }
      }

      const TOURNAMENT_MAX_LENGTHS = {
        type: 20,
        name: 250,
        startTime: 100,
        endTime: 50,
        status: 15,
        location: 255,
        elementPosition: 50
      };

      // Base interface for tournament data

      // Base class with shared functionality
      class BaseTournament {
        constructor(data) {
          // Validate required fields
          if (!data.tournamentId) {
            throw new ValidationError('tournamentId', 'Field is required');
          }
          //min and max  value
          if (data.tournamentId < 0 || data.tournamentId > 99999999999) {
            throw new ValidationError('tournamentId', 'Field must be between min value:0 and max value:99999999999');
          }
          if (data.tournamentPosition < 1 || data.tournamentPosition > 30) {
            throw new ValidationError('tournamentPosition', 'Field must be between min value:1 and max value:30');
          }

          // Validate status type
          const validStatuses = ['active', 'upcoming', 'finished'];
          const normalizedStatus = (data.status || '').toLowerCase();
          if (!validStatuses.includes(normalizedStatus)) {
            throw new ValidationError('status', `Incorrect Status Type,must be one of: ${validStatuses.join(', ')}`);
          }

          //Validate max lengths
          if (data.tournamentName && data.tournamentName.length > TOURNAMENT_MAX_LENGTHS.name) {
            throw new ValidationError('tournamentName', `Field length exceeds maximum of ${TOURNAMENT_MAX_LENGTHS.name} characters`);
          }
          if (data.status && data.status.length > TOURNAMENT_MAX_LENGTHS.status) {
            throw new ValidationError('status', `Field length exceeds maximum of ${TOURNAMENT_MAX_LENGTHS.status} characters`);
          }
          if (data.startTime && data.startTime.length > TOURNAMENT_MAX_LENGTHS.startTime) {
            throw new ValidationError('startTime', `Field length exceeds maximum of ${TOURNAMENT_MAX_LENGTHS.startTime} characters`);
          }
          if (data.endTime && data.endTime.length > TOURNAMENT_MAX_LENGTHS.endTime) {
            throw new ValidationError('endTime', `Field length exceeds maximum of ${TOURNAMENT_MAX_LENGTHS.endTime} characters`);
          }
          if (data.location && data.location.length > TOURNAMENT_MAX_LENGTHS.location) {
            throw new ValidationError('location', `Field length exceeds maximum of ${TOURNAMENT_MAX_LENGTHS.location} characters`);
          }
          if (data.elementPosition && data.elementPosition.length > TOURNAMENT_MAX_LENGTHS.elementPosition) {
            throw new ValidationError('elementPosition', `Field length exceeds maximum of ${TOURNAMENT_MAX_LENGTHS.elementPosition} characters`);
          }

          // Data type validation
          if (typeof data.tournamentId !== 'number') {
            throw new ValidationError('tournamentId', 'Field must be a number');
          }
          if (data.tournamentName && typeof data.tournamentName !== 'string') {
            throw new ValidationError('tournamentName', 'Field must be a string');
          }
          if (data.status && typeof data.status !== 'string') {
            throw new ValidationError('status', 'Field must be a string');
          }
          if (data.startTime && typeof data.startTime !== 'string') {
            throw new ValidationError('startTime', 'Field must be a string');
          }
          if (data.endTime && typeof data.endTime !== 'string') {
            throw new ValidationError('endTime', 'Field must be a string');
          }
          if (data.location && typeof data.location !== 'string') {
            throw new ValidationError('location', 'Field must be a string');
          }
          if (data.elementPosition && typeof data.elementPosition !== 'string') {
            throw new ValidationError('elementPosition', 'Field must be a string');
          }
          /*  if (data.gameIds && !Array.isArray(data.gameIds)) {
                throw new ValidationError('gameIds', 'Field must be an array');
            }
            if (data.gameNames && !Array.isArray(data.gameNames)) {
                throw new ValidationError('gameNames', 'Field must be an array');
            }*/
          if (data.tournamentPosition && typeof data.tournamentPosition !== 'number') {
            throw new ValidationError('tournamentPosition', 'Field must be a number');
          }
          this.tournamentId = data.tournamentId;
          this.tournamentName = data.tournamentName;
          this.status = normalizedStatus;
          this.type = (data.type || '').toLowerCase();
          this.startTime = data.startTime || null;
          this.endTime = data.endTime || null;
          this.location = data.location || null;
          this.elementPosition = data.elementPosition || null;
          this.gameIds = data.gameIds || null;
          this.gameNames = data.gameNames || null;
          this.tournamentPosition = data.tournamentPosition || null;
        }
        toJSON() {
          return {
            id: this.tournamentId,
            name: this.tournamentName,
            startTime: this.startTime,
            endTime: this.endTime,
            status: this.status,
            type: this.type,
            gameIds: this.gameIds,
            gameNames: this.gameNames,
            location: this.location,
            elementPosition: this.elementPosition,
            tournamentPosition: this.tournamentPosition
          };
        }
      }
      class TournamentView extends BaseTournament {
        //fromEventData comes in from the actual FE payload
        static fromEventData(data) {
          var _data$detail;
          return new TournamentView({
            tournamentId: data.tournamentId,
            tournamentName: data.tournamentName,
            status: data.status,
            type: 'view',
            startTime: data.tournamentStartDate ? data.tournamentStartDate.toString() : null,
            endTime: data.tournamentEndsIn ? data.tournamentEndsIn.toString() : null,
            location: data.location || ((_data$detail = data.detail) === null || _data$detail === void 0 ? void 0 : _data$detail.location) || null,
            gameIds: data.gamesInTournament || null,
            gameNames: data.gamesNamesInTournament || null,
            elementPosition: data.elementPosition || null,
            tournamentPosition: data.tournamentPosition === 0 ? 1 : data.tournamentPosition || null
          });
        }
        send(id, name, startTime, endTime, status, type, gameIds, gameNames, location, elementPosition, tournamentPosition) {
          const sender = new UniversalAnalyticsSender();
          sender.send('tournamentInteraction', {
            id: this.tournamentId,
            name: this.tournamentName,
            startTime: this.startTime,
            endTime: this.endTime,
            status: this.status,
            type: this.type,
            gameIds: this.gameIds,
            gameNames: this.gameNames,
            location: this.location,
            elementPosition: this.elementPosition,
            tournamentPosition: this.tournamentPosition
          });
        }
      } exports('c', TournamentView);

      // TournamentOptIn class
      class TournamentOptIn extends BaseTournament {
        //fromEventData comes in from the actual FE payload
        static fromEventData(data) {
          var _data$detail2;
          return new TournamentOptIn({
            tournamentId: data.tournamentId,
            tournamentName: data.tournamentName,
            status: data.status,
            type: 'opt in',
            startTime: data.tournamentStartDate ? data.tournamentStartDate.toString() : null,
            endTime: data.tournamentEndsIn ? data.tournamentEndsIn.toString() : null,
            location: data.location || ((_data$detail2 = data.detail) === null || _data$detail2 === void 0 ? void 0 : _data$detail2.location) || null,
            gameIds: data.gamesInTournament || null,
            gameNames: data.gamesNamesInTournament || null,
            elementPosition: data.elementPosition || null,
            tournamentPosition: data.tournamentPosition === 0 ? 1 : data.tournamentPosition || null
          });
        }
        send(id, name, startTime, endTime, status, type, gameIds, gameNames, location, elementPosition, tournamentPosition) {
          const sender = new UniversalAnalyticsSender();
          sender.send('tournamentInteraction', {
            id: this.tournamentId,
            name: this.tournamentName,
            startTime: this.startTime,
            endTime: this.endTime,
            status: this.status,
            type: this.type,
            gameIds: this.gameIds,
            gameNames: this.gameNames,
            location: this.location,
            elementPosition: this.elementPosition,
            tournamentPosition: this.tournamentPosition
          });
        }
      } exports('T', TournamentOptIn);

      const REGISTRATION_MAX_LENGTHS = {
        name: 255,
        method: 255,
        order: 50,
        processId: 255,
        additionalInfo: 1024
      };
      class RegistrationSession {
        constructor(data) {
          // Validate required fields
          if (!data.name) {
            throw new ValidationError('name', 'Field is required');
          }
          if (!data.order) {
            throw new ValidationError('order', 'Field is required');
          }
          if (!data.processId) {
            throw new ValidationError('processId', 'Field is required');
          }
          if (!data.method) {
            throw new ValidationError('method', 'Field is required');
          }

          //min and max value
          if (data.order < 0 || data.order > 50) {
            throw new ValidationError('order', 'Field must be between min value:0 and max value:50');
          }
          // Validate max lengths
          if (data.name && data.name.length > REGISTRATION_MAX_LENGTHS.name) {
            throw new ValidationError('name', `Field length exceeds maximum of ${REGISTRATION_MAX_LENGTHS.name} characters`);
          }
          if (data.method && data.method.length > REGISTRATION_MAX_LENGTHS.method) {
            throw new ValidationError('method', `Field length exceeds maximum of ${REGISTRATION_MAX_LENGTHS.method} characters`);
          }
          if (data.order && data.order > REGISTRATION_MAX_LENGTHS.order) {
            throw new ValidationError('order', `Field value exceeds maximum of ${REGISTRATION_MAX_LENGTHS.order}`);
          }
          if (data.processId && data.processId.length > REGISTRATION_MAX_LENGTHS.processId) {
            throw new ValidationError('processId', `Field length exceeds maximum of ${REGISTRATION_MAX_LENGTHS.processId} characters`);
          }
          if (data.additionalInfo && data.additionalInfo.length > REGISTRATION_MAX_LENGTHS.additionalInfo) {
            throw new ValidationError('additionalInfo', `Field length exceeds maximum of ${REGISTRATION_MAX_LENGTHS.additionalInfo} characters`);
          }
          // Type validation
          if (typeof data.name !== 'string') {
            throw new ValidationError('name', 'Field must be a string');
          }
          if (typeof data.method !== 'string') {
            throw new ValidationError('method', 'Field must be a string');
          }
          if (typeof data.order !== 'number') {
            throw new ValidationError('order', 'Field must be a number');
          }
          if (typeof data.processId !== 'string') {
            throw new ValidationError('processId', 'Field must be a string');
          }
          if (data.additionalInfo && typeof data.additionalInfo !== 'string') {
            throw new ValidationError('additionalInfo', 'Field must be a string');
          }
          this.name = data.name;
          this.method = data.method;
          this.order = data.order;
          this.nameEncountered = data.nameEncountered;
          this.orderEncountered = data.orderEncountered;
          this.processId = data.processId;
          this.additionalInfo = data.additionalInfo;
        }
        //fromEventData comes in from the actual FE payload
        static fromEventData(data) {
          return new RegistrationSession({
            name: data.name,
            method: data.method,
            order: data.order,
            nameEncountered: data.nameEncountered || [],
            orderEncountered: data.orderEncountered || [],
            processId: data.processId,
            additionalInfo: data.additionalInfo || ''
          });
        }
        toJSON() {
          return {
            name: this.name,
            method: this.method,
            order: this.order,
            nameEncountered: this.nameEncountered,
            orderEncountered: this.orderEncountered,
            processId: this.processId,
            additionalInfo: this.additionalInfo
          };
        }
        send() {
          const sender = new UniversalAnalyticsSender();
          sender.send('registration', {
            name: this.name,
            method: this.method,
            order: this.order,
            orderEncountered: this.orderEncountered,
            nameEncountered: this.nameEncountered,
            processId: this.processId,
            additionalInfo: this.additionalInfo
          });
        }
      }

      const VERIFICATION_MAX_LENGTHS = {
        type: 50,
        documentType: 100,
        documentUploadStatus: 25,
        authenticationProvider: 25,
        verificationType: 25,
        verificationProcess: 50,
        viewCategory: 20
      };

      // Base interface for verification data

      // Base class with shared functionality
      class BaseVerification {
        constructor(data) {
          // Validate required fields
          if (!data.type) {
            throw new ValidationError('type', 'Field is required');
          }

          // Validate field lengths
          if (data.type && data.type.length > VERIFICATION_MAX_LENGTHS.type) {
            throw new ValidationError('type', `Field length exceeds maximum of ${VERIFICATION_MAX_LENGTHS.type} characters`);
          }
          if (data.documentType && data.documentType.length > VERIFICATION_MAX_LENGTHS.documentType) {
            throw new ValidationError('documentType', `Field length exceeds maximum of ${VERIFICATION_MAX_LENGTHS.documentType} characters`);
          }
          if (data.documentUploadStatus && data.documentUploadStatus.length > VERIFICATION_MAX_LENGTHS.documentUploadStatus) {
            throw new ValidationError('documentUploadStatus', `Field length exceeds maximum of ${VERIFICATION_MAX_LENGTHS.documentUploadStatus} characters`);
          }
          if (data.authenticationProvider && data.authenticationProvider.length > VERIFICATION_MAX_LENGTHS.authenticationProvider) {
            throw new ValidationError('authenticationProvider', `Field length exceeds maximum of ${VERIFICATION_MAX_LENGTHS.authenticationProvider} characters`);
          }
          if (data.verificationType && data.verificationType.length > VERIFICATION_MAX_LENGTHS.verificationType) {
            throw new ValidationError('verificationType', `Field length exceeds maximum of ${VERIFICATION_MAX_LENGTHS.verificationType} characters`);
          }
          if (data.verificationProcess && data.verificationProcess.length > VERIFICATION_MAX_LENGTHS.verificationProcess) {
            throw new ValidationError('verificationProcess', `Field length exceeds maximum of ${VERIFICATION_MAX_LENGTHS.verificationProcess} characters`);
          }
          if (data.viewCategory && data.viewCategory.length > VERIFICATION_MAX_LENGTHS.viewCategory) {
            throw new ValidationError('viewCategory', `Field length exceeds maximum of ${VERIFICATION_MAX_LENGTHS.viewCategory} characters`);
          }
          // Validate data types
          if (data.type && typeof data.type !== 'string') {
            throw new ValidationError('type', 'Field must be a string');
          }
          if (data.documentType && typeof data.documentType !== 'string') {
            throw new ValidationError('documentType', 'Field must be a string');
          }
          if (data.documentUploadStatus && typeof data.documentUploadStatus !== 'string') {
            throw new ValidationError('documentUploadStatus', 'Field must be a string');
          }
          if (data.authenticationProvider && typeof data.authenticationProvider !== 'string') {
            throw new ValidationError('authenticationProvider', 'Field must be a string');
          }
          if (data.verificationType && typeof data.verificationType !== 'string') {
            throw new ValidationError('verificationType', 'Field must be a string');
          }
          if (data.verificationProcess && typeof data.verificationProcess !== 'string') {
            throw new ValidationError('verificationProcess', 'Field must be a string');
          }
          if (data.viewCategory && typeof data.viewCategory !== 'string') {
            throw new ValidationError('viewCategory', 'Field must be a string');
          }
          this.type = data.type;
          this.documentType = data.documentType || null;
          this.documentUploadStatus = data.documentUploadStatus || null;
          this.authenticationProvider = data.authenticationProvider || null;
          this.verificationType = data.verificationType || null;
          this.verificationProcess = data.verificationProcess || null;
          this.viewCategory = data.viewCategory || null;
        }
        toJSON() {
          return {
            type: this.type,
            documentType: this.documentType,
            documentUploadStatus: this.documentUploadStatus,
            authenticationProvider: this.authenticationProvider,
            verificationType: this.verificationType,
            verificationProcess: this.verificationProcess,
            viewCategory: this.viewCategory
          };
        }
      }
      class VerificationEvent extends BaseVerification {
        //fromEventData comes in from the actual FE payload
        static fromEventData(data) {
          return new VerificationEvent({
            type: data.type,
            documentType: data.documentType || null,
            documentUploadStatus: data.documentUploadStatus || null,
            authenticationProvider: data.authenticationProvider || null,
            verificationType: data.verificationType || null,
            verificationProcess: data.verificationProcess || null,
            viewCategory: data.viewCategory || null
          });
        }

        //fromADCPayload is mapping of FE payload to the field names used within ADC miniapp 
        static fromADCPayload(data) {
          const mappedData = {
            type: data.event_category,
            documentType: data.event_sub_category,
            documentUploadStatus: data.documentUploadStatus || null,
            authenticationProvider: data.provider_name || null,
            verificationType: data.verification_type || null,
            verificationProcess: data.verification_process || null,
            viewCategory: data.view_category || null
          };
          return new VerificationEvent(mappedData);
        }
        send(type, documentType, documentUploadStatus, authenticationProvider, verificationType, verificationProcess) {
          const sender = new UniversalAnalyticsSender();
          sender.send('verificationInteraction', {
            type: type,
            documentType: this.documentType,
            documentUploadStatus: this.documentUploadStatus,
            authenticationProvider: this.authenticationProvider,
            verificationType: this.verificationType,
            verificationProcess: this.verificationProcess,
            viewCategory: this.viewCategory
          });
        }
      } exports('V', VerificationEvent);

      const LOGIN_MAX_LENGTHS = {
        type: 100,
        method: 100,
        ctaClicked: 100,
        widget_name: 100
      };
      class BaseLogin {
        constructor(data) {
          var _data$is_first_login, _data$marketingConsen;
          // Validate required fields
          if (!data.type) {
            throw new ValidationError('type', 'Field is required');
          }

          // Validate type enum
          const validTypes = ['appeared', 'closed', 'ctaclicked', 'eauth start', 'error', 'passwordresetemailsubmit', 'passwordresetsubmit', 'success'];
          if (!validTypes.includes(data.type)) {
            throw new ValidationError('type', `Incorrect Type, must be one of: ${validTypes.join(', ')}`);
          }

          // Validate lengths
          if (data.type && data.type.length > LOGIN_MAX_LENGTHS.type) {
            throw new ValidationError('type', `Field length exceeds maximum of ${LOGIN_MAX_LENGTHS.type} characters`);
          }
          if (data.method && data.method.length > LOGIN_MAX_LENGTHS.method) {
            throw new ValidationError('method', `Field length exceeds maximum of ${LOGIN_MAX_LENGTHS.method} characters`);
          }
          if (data.ctaClicked && data.ctaClicked.length > LOGIN_MAX_LENGTHS.ctaClicked) {
            throw new ValidationError('ctaClicked', `Field length exceeds maximum of ${LOGIN_MAX_LENGTHS.ctaClicked} characters`);
          }
          if (data.widget_name && data.widget_name.length > LOGIN_MAX_LENGTHS.widget_name) {
            throw new ValidationError('widget_name', `Field length exceeds maximum of ${LOGIN_MAX_LENGTHS.widget_name} characters`);
          }

          // Validate data types
          if (data.method && typeof data.method !== 'string') {
            throw new ValidationError('method', 'Field must be a string');
          }
          if (data.ctaClicked && typeof data.ctaClicked !== 'string') {
            throw new ValidationError('ctaClicked', 'Field must be a string');
          }
          if (data.widget_name && typeof data.widget_name !== 'string') {
            throw new ValidationError('widget_name', 'Field must be a string');
          }
          if (typeof data.is_first_login !== 'undefined' && data.is_first_login !== null && typeof data.is_first_login !== 'boolean') {
            throw new ValidationError('is_first_login', 'Field must be a boolean');
          }
          if (data.is_first_login === true) {
            throw new ValidationError('is_first_login', 'Field must be false');
          }
          this.type = data.type;
          this.method = data.method || null;
          this.ctaClicked = data.ctaClicked || null;
          this.widget_name = data.widget_name || null;
          this.is_first_login = (_data$is_first_login = data.is_first_login) !== null && _data$is_first_login !== void 0 ? _data$is_first_login : null;
          this.marketingConsent = (_data$marketingConsen = data.marketingConsent) !== null && _data$marketingConsen !== void 0 ? _data$marketingConsen : null;
        }
        toJSON() {
          return {
            type: this.type,
            method: this.method,
            ctaClicked: this.ctaClicked,
            widget_name: this.widget_name,
            is_first_login: this.is_first_login,
            marketingConsent: this.marketingConsent
          };
        }
      }
      class LoginEvent extends BaseLogin {
        static fromEventData(data) {
          return new LoginEvent({
            type: data.type,
            method: data.method || null,
            ctaClicked: data.ctaClicked || null,
            widget_name: data.widget_name || null,
            is_first_login: data.is_first_login,
            marketingConsent: data.marketingConsent
          });
        }

        // Map ADC/FE payload to internal model
        static fromADCPayload(data) {
          var _data$type, _ref, _data$method, _ref2, _data$ctaClicked, _data$widget_name;
          const mapped = {
            type: String(((_data$type = data.type) !== null && _data$type !== void 0 ? _data$type : data.login_type) || '').toLowerCase(),
            method: (_ref = (_data$method = data.method) !== null && _data$method !== void 0 ? _data$method : data.login_method) !== null && _ref !== void 0 ? _ref : null,
            ctaClicked: (_ref2 = (_data$ctaClicked = data.ctaClicked) !== null && _data$ctaClicked !== void 0 ? _data$ctaClicked : data.widget_cta_name) !== null && _ref2 !== void 0 ? _ref2 : null,
            widget_name: (_data$widget_name = data.widget_name) !== null && _data$widget_name !== void 0 ? _data$widget_name : null,
            is_first_login: data.is_first_login,
            marketingConsent: data.marketingConsent
          };
          return new LoginEvent(mapped);
        }
        send() {
          const sender = new UniversalAnalyticsSender();
          sender.send('login', {
            type: this.type,
            method: this.method,
            ctaClicked: this.ctaClicked,
            widget_name: this.widget_name,
            is_first_login: this.is_first_login,
            marketingConsent: this.marketingConsent
          });
        }
      } exports('L', LoginEvent);

      const CONTROLS_AND_LIMIT_MAX_LENGTHS = {
        type: 50,
        limitType: 100,
        limitSubType: 100,
        timeframe: 50,
        value: 300,
        product: 50
      };

      // Base interface for controls and limits data

      // Base class with shared functionality
      class BaseControlsAndLimit {
        constructor(data) {
          // Validate required fields
          if (!data.type) {
            throw new ValidationError('type', 'Field is required');
          }
          if (!data.limitType) {
            throw new ValidationError('limitType', 'Field is required');
          }
          if (!data.limitSubType) {
            throw new ValidationError('limitSubType', 'Field is required');
          }

          // Validate type enum
          const validTypes = ['limit applied', 'limit modified', 'limit confirmed', 'limit removed', 'request cancelled', 'limit selected', 'limit start', 'limit set failed', 'limit cancelled', 'request cancelled failed', 'limit removed failed'];
          if (!validTypes.includes(data.type)) {
            throw new ValidationError('type', `Incorrect Type, must be one of: ${validTypes.join(', ')}`);
          }

          // Validate field lengths
          if (data.type && data.type.length > CONTROLS_AND_LIMIT_MAX_LENGTHS.type) {
            throw new ValidationError('type', `Field length exceeds maximum of ${CONTROLS_AND_LIMIT_MAX_LENGTHS.type} characters`);
          }
          if (data.limitType && data.limitType.length > CONTROLS_AND_LIMIT_MAX_LENGTHS.limitType) {
            throw new ValidationError('limitType', `Field length exceeds maximum of ${CONTROLS_AND_LIMIT_MAX_LENGTHS.limitType} characters`);
          }
          if (data.limitSubType && data.limitSubType.length > CONTROLS_AND_LIMIT_MAX_LENGTHS.limitSubType) {
            throw new ValidationError('limitSubType', `Field length exceeds maximum of ${CONTROLS_AND_LIMIT_MAX_LENGTHS.limitSubType} characters`);
          }
          if (data.timeframe && data.timeframe.length > CONTROLS_AND_LIMIT_MAX_LENGTHS.timeframe) {
            throw new ValidationError('timeframe', `Field length exceeds maximum of ${CONTROLS_AND_LIMIT_MAX_LENGTHS.timeframe} characters`);
          }
          if (data.value && data.value.length > CONTROLS_AND_LIMIT_MAX_LENGTHS.value) {
            throw new ValidationError('value', `Field length exceeds maximum of ${CONTROLS_AND_LIMIT_MAX_LENGTHS.value} characters`);
          }
          if (data.product && data.product.length > CONTROLS_AND_LIMIT_MAX_LENGTHS.product) {
            throw new ValidationError('product', `Field length exceeds maximum of ${CONTROLS_AND_LIMIT_MAX_LENGTHS.product} characters`);
          }
          //Validate data types
          if (data.type && typeof data.type !== 'string') {
            throw new ValidationError('type', 'Field must be a string');
          }
          if (data.limitType && typeof data.limitType !== 'string') {
            throw new ValidationError('limitType', 'Field must be a string');
          }
          if (data.limitSubType && typeof data.limitSubType !== 'string') {
            throw new ValidationError('limitSubType', 'Field must be a string');
          }
          if (data.timeframe && typeof data.timeframe !== 'string') {
            throw new ValidationError('timeframe', 'Field must be a string');
          }
          if (data.value && typeof data.value !== 'string') {
            throw new ValidationError('value', 'Field must be a string');
          }
          if (data.product && typeof data.product !== 'string') {
            throw new ValidationError('product', 'Field must be a string');
          }
          this.type = data.type;
          this.limitType = data.limitType;
          this.limitSubType = data.limitSubType;
          this.timeframe = data.timeframe || null;
          this.value = data.value || null;
          this.product = data.product || null;
        }
        toJSON() {
          return {
            type: this.type,
            limitType: this.limitType,
            limitSubType: this.limitSubType,
            timeframe: this.timeframe,
            value: this.value,
            product: this.product
          };
        }
      }
      class ControlsAndLimitEvent extends BaseControlsAndLimit {
        //fromEventData comes in from the actual FE payload
        static fromEventData(data) {
          return new ControlsAndLimitEvent({
            type: data.type,
            limitType: data.limitType,
            limitSubType: data.limitSubType,
            timeframe: data.timeframe,
            value: data.value,
            product: data.product
          });
        }

        //fromADCPayload is mapping of FE payload to the field names used within ADC miniapp 
        static fromADCPayload(data) {
          // Map backend payload format to internal format
          const mappedData = {
            type: String(data.control_event || "undefined").replace(/_/ig, " ").replace("undefined", "limit"),
            limitType: data.limit_type || data.limitType,
            limitSubType: data.limit_subtype || data.limitSubType,
            timeframe: data.limit_timeframe || data.timeframe,
            value: data.limit_value || data.value,
            product: data.limit_product || data.product || 'casino' // Default product
          };
          return new ControlsAndLimitEvent(mappedData);
        }
        send(type, limitType, limitSubType, timeframe, value, product) {
          const sender = new UniversalAnalyticsSender();
          sender.send('controlsAndLimit', {
            type: this.type,
            limitType: this.limitType,
            limitSubType: this.limitSubType,
            timeframe: this.timeframe,
            value: this.value,
            product: this.product
          });
        }
      } exports('C', ControlsAndLimitEvent);

      function registrationEvents(eventName, data) {
        if (eventName === 'open registration') {
          return;
        }
        if (eventName === "registrationWelcomeOfferInteraction") {
          welcomeOfferInteraction(eventName, data);
        } else if (eventName === "registrationStart") {
          registrationStart(eventName, data);
        } else if (eventName === "registrationSteps") {
          registrationSteps(eventName, data);
        } else if (/registrationSuccessful/i.test(eventName)) {
          registrationSuccess(data);
        } else if (eventName === "registrationFallback") {
          registrationFallback(eventName, data);
        } else if (eventName === "registrationButtonJWT") {
          registration_steps_server_call(data, "eauth start", "");
        } else if (eventName === "registrationButtonIDin") {
          registration_steps_server_call(data, "eauth start", "idin");
        } else if (eventName === 'error') {
          registrationError(data);
        } else if (eventName === 'registrationInteraction') {
          registrationInteraction(eventName, data);
        }
      }
      function registrationInteraction(eventName, data) {
        try {
          let processId = analyticsHelpers.storageManagement._getStorage("sessionStorage", "processId") || {};
          let eauthErrorCheck = false;
          let names = analyticsHelpers.storageManagement._getStorage("sessionStorage", "registrationInteraction") || [];
          let previousStep = names[names.length - 1];
          if (data.name === "registration_error" && /eauth/i.test(data.method) && previousStep === "idprovider_return_step" || data.name === 'registration_type_selection' && previousStep === "registration_error") {
            eauthErrorCheck = true;
          }
          if (processId !== data.processId && !eauthErrorCheck) {
            analyticsHelpers.storageManagement._deleteStorage("sessionStorage", "registrationInteraction");
            analyticsHelpers.storageManagement._deleteStorage("sessionStorage", "orderEncountered");
            analyticsHelpers.storageManagement._deleteStorage("sessionStorage", "processId");
          }
          let nameEncountered = analyticsHelpers.storageManagement._getStorage("sessionStorage", "registrationInteraction") || [];
          let orderEncountered = analyticsHelpers.storageManagement._getStorage("sessionStorage", "orderEncountered") || [];
          nameEncountered.push(data.name);
          orderEncountered.push(data.order);
          analyticsHelpers.storageManagement._setStorage("sessionStorage", "registrationInteraction", nameEncountered);
          analyticsHelpers.storageManagement._setStorage("sessionStorage", "orderEncountered", orderEncountered);
          analyticsHelpers.storageManagement._setStorage("sessionStorage", "processId", data.processId);
          if (nameEncountered.length === 1) {
            data.additionalInfo = "Start";
            marketingHandler('registrationStart', data);
          }
          if (analyticsHelpers.getCookie('isReturningUser')) {
            if (data !== null && data !== void 0 && data.additionalInfo) {
              data.additionalInfo = data.additionalInfo + '~returning_user';
            } else {
              data.additionalInfo = 'returning_user';
            }
          }
          if (analyticsHelpers.storageManagement._getStorage("sessionStorage", "registration_experiment")) {
            if (typeof data.additionalInfo !== "undefined") {
              data.additionalInfo = data.additionalInfo + " | " + analyticsHelpers.storageManagement._getStorage("sessionStorage", "registration_experiment");
            } else {
              data.additionalInfo = analyticsHelpers.storageManagement._getStorage("sessionStorage", "registration_experiment");
            }
          }
          let legacyStepNames = {
            "registration_start": "registration start",
            "intent": "intent",
            "step_one": "step 1",
            "step_two": "step 2",
            "step_three": "step 3",
            "step_four": "step 4",
            "welcome_bonus_step": "welcome offer screen",
            "registration_successful": "success",
            "registration_error": "error",
            "registration_type_selection": "eauth screen",
            "idprovider_step_one": "eauth last step"
          };
          let legacyName = legacyStepNames[data.name] || "";
          if (data.name === "registration_type_selected" && /eauth/i.test(data.method)) {
            legacyName = "eauth start";
          }
          const {
            market
          } = useDataLayer();
          let schema_to_send = {
            event: {
              schema: getSnowplowSchemaURI("registrationSession"),
              data: RegistrationSession.fromEventData({
                "name": data.name,
                "method": data.method,
                "order": data.order,
                "nameEncountered": nameEncountered,
                "orderEncountered": orderEncountered,
                "processId": data.processId,
                "additionalInfo": data.additionalInfo
              })
            },
            context: [
            //in place as apps do not support market context
            {
              schema: getSnowplowSchemaURI("genericInteraction"),
              data: {
                "type": 'temp-app-reg-debug',
                "value": window.location.href.substring(0, 200),
                "additionalInfo": market
              }
            }]
          };
          if (legacyName) {
            schema_to_send.context.push({
              schema: getSnowplowSchemaURI("registration"),
              data: {
                type: legacyName,
                method: data.method,
                additionalDetails: data.additionalInfo
              }
            });
          }
          if (data.name === "registration_successful") {
            const {
              sessionId
            } = useDataLayer();
            let optIn = false;
            if (data !== null && data !== void 0 && data.communicationSelected && data.communicationSelected.length > 0) {
              optIn = true;
            }
            schema_to_send.context.push({
              schema: getSnowplowSchemaURI("registrationComms"),
              data: {
                "communicationOptin": optIn,
                "communicationSelected": data.communicationSelected
              }
            }, {
              schema: getSnowplowSchemaURI('login'),
              data: {
                "type": "success",
                // appeared, CTAClicked, closed, success, error
                "method": "registration",
                "ctaClicked": "registration",
                "widget_name": "registration",
                "is_first_login": true
              }
            });
            let offer = analyticsHelpers.storageManagement._getStorage("sessionStorage", "registrationOffer");
            if (offer) {
              let offerId = offer.split("~")[0];
              let offerStatus = offer.split("~")[1];
              schema_to_send.context.push({
                schema: getSnowplowSchemaURI("offer"),
                data: {
                  "offerId": parseInt(offerId),
                  "name": "",
                  "accepted": true
                }
              });
            }
            try {
              marketingHandler("registrationSuccessful", data);
            } catch (error) {}
            window.snowplow('clearGlobalContexts');
          }
          if (data.name === "error") {
            schema_to_send.event = {
              schema: getSnowplowSchemaURI("registration"),
              data: {
                type: data.name,
                method: data.method,
                additionalDetails: data.additionalInfo.error
              }
            };
          }
          if (data !== null && data !== void 0 && data.deposit) {
            schema_to_send.context.push({
              schema: getSnowplowSchemaURI("deposit"),
              data: {
                "type": data.deposit.type,
                "count": data.deposit.count,
                "amount": data.deposit.amount,
                "method": data.deposit.method,
                "currency": data.deposit.currency,
                "id": parseInt(data.deposit.id) || null
              }
            });
          }
          if (data !== null && data !== void 0 && data.controls_and_limits) {
            for (let i = 0; i < data.controls_and_limits.length; i++) {
              schema_to_send.context.push({
                schema: getSnowplowSchemaURI("controlsAndLimits"),
                data: {
                  "type": data.controls_and_limits[i].type,
                  "limitType": data.controls_and_limits[i].limit_type,
                  "limitSubType": data.controls_and_limits[i].limit_subtype,
                  "timeframe": data.controls_and_limits[i].timeframe,
                  "value": data.controls_and_limits[i].value + "",
                  "product": data.controls_and_limits[i].product
                }
              });
            }
          }
          if (data !== null && data !== void 0 && data.verification) {
            schema_to_send.context.push({
              schema: getSnowplowSchemaURI("verification"),
              data: {
                "type": data.verification.type,
                "documentType": data.verification.document_type,
                "documentUploadStatus": data.verification.document_upload_status,
                "authenticationProvider": data.verification.authentication_provider,
                "verificationType": data.verification.verification_type,
                "verificationProcess": data.verification.verification_process
              }
            });
          }
          fireSnowplowEvent(schema_to_send, data);
        } catch (error) {
          console.error(`RegistrationSession validation error: ${error.field} - ${error.message}`);
          return;
        }
      }

      /* *** registration helpers start *** */
      function help_fire_snowplow(type, method, additionalDetails) {
        // Mechanism to prevent double firing
        const namespace = "registrationStepsAnalytics";

        // Deletes storage when you leave the registration page
        window.addEventListener('beforeunload', e => {
          const currentPage = window.location.pathname;
          if (currentPage === '/registration') {
            analyticsHelpers.storageManagement._deleteStorage("sessionStorage", namespace);
          }
        });

        // list of steps that have been fired, e.g. eauth screen, step 1, intent.
        let firedEvents = analyticsHelpers.storageManagement._getStorage("sessionStorage", namespace);
        if (!firedEvents) {
          firedEvents = {};
        }
        if (firedEvents[type]) {
          return;
        }
        firedEvents[type] = true;
        analyticsHelpers.storageManagement._setStorage("sessionStorage", namespace, firedEvents);
        if (/Last_?Step/i.test(type)) {
          type = "eauth last step";
        }
        const {
          market
        } = useDataLayer();
        let schema_to_send = {
          event: {
            schema: getSnowplowSchemaURI('registration'),
            data: {
              type: type,
              method: method,
              additionalDetails: additionalDetails || null
            }
          },
          //added below genericInteraction schema as a short term fix for CIOSC-1834
          context: [{
            schema: getSnowplowSchemaURI("genericInteraction"),
            data: {
              "type": 'temp-app-reg-debug',
              "value": window.location.href.substring(0, 200),
              "additionalInfo": market
            }
          }]
        };
        if (!(type === 'welcome offer screen' && window.location.pathname === '/myaccount/mymoney/cashier')) {
          fireSnowplowEvent(schema_to_send);
        }
      }
      function registrationError(data) {
        const {
          market
        } = useDataLayer();
        var validationErrors = data.validationErrors || [];
        var validationMessage = "";
        for (var i = 0; i < validationErrors.length; i++) {
          if (validationErrors[i].fieldQualifiedName) {
            validationMessage = validationMessage + "~" + validationErrors[i].fieldQualifiedName + ":" + (validationErrors[i].fieldReason || "");
            validationMessage = validationMessage.trim();
          }
        }
        let message = "error message unaivalable";
        let erroCode = "code unaivalable";
        if (validationMessage !== "") message = validationMessage;
        if (data.errorName) message = data.errorName;
        if (data.errorCode) erroCode = data.errorCode;
        if (data.errorStatus) erroCode = data.errorStatus;
        let schema_to_send = {
          event: {
            schema: getSnowplowSchemaURI('registration'),
            data: {
              type: 'error',
              method: data.registration_method || "manual"
            }
          },
          context: [{
            schema: getSnowplowSchemaURI('error'),
            data: {
              "type": "registration error",
              "product": "registration",
              "code": erroCode,
              "message": message
            }
          }, {
            schema: getSnowplowSchemaURI("genericInteraction"),
            data: {
              "type": 'temp-app-reg-debug',
              "value": window.location.href.substring(0, 200),
              "additionalInfo": market
            }
          }]
        };
        fireSnowplowEvent(schema_to_send);
      }
      function registration_steps_server_call(data, currentStep, method) {
        currentStep = !currentStep ? data.currentStep : currentStep;
        method = !method ? data.registration_method : method;
        method = /criipto/i.test(method) ? "nemid_mitid" : method;
        window._registration_method = method || "manual";
        let step = "step " + (currentStep + "").replace(/^step/, "");
        if (/Last_?Step/i.test(currentStep)) {
          if (/idin/i.test(currentStep)) {
            return false;
          }
          step = "eauth last step";
        }
        if (currentStep === "welcome offer screen") {
          if (window.location.pathname.includes("registration")) {
            return;
          } else if (!/cashier/.test(window.location.pathname)) {
            step = 'welcome offer banner';
          }
        }
        if (/step1/i.test(currentStep) || /eauth start/i.test(currentStep)) {
          if (getMarketingConsent()) {
            marketingHandler("registrationStart", data);
          }
        }
        if (/screen|eauth/i.test(currentStep)) {
          step = currentStep;
        }
        /* capture the customer bank on idin registration bank */
        let bankSelected = null;
        if (data.registration_bank) {
          var bank_mapping = {
            "ABNANL2A": "ABN AMRO",
            "ASNBNL21": "ASN Bank",
            "BUNQNL2A": "bunq",
            "INGBNL2A": "ING",
            "RABONL2U": "Rabobank",
            "RBRBNL21": "RegioBank",
            "SNSBNL2A": "SNS",
            "TRIONL2U": "Triodos Bank"
          };
          bankSelected = bank_mapping[data.registration_bank] || data.registration_bank;
        }
        help_fire_snowplow(step, method, bankSelected);
      }

      /* *** registration helpers end *** */

      /* *** registration functions start *** */

      function registrationStart(eventName, data) {
        let registrationMethods = {
          idin: {
            regex: /^idin|manual$/i,
            host: /unibet\.(eu|nl)/i,
            step: "eauth screen"
          },
          /* legacy implementation */
          itsme: {
            regex: /^itsme$/i,
            host: /unibet(casino|sports|games)?\.be/i,
            step: "eauth start"
          },
          /* itsme implementation */
          tupas: {
            regex: /^tupas|manual$/i,
            host: /(?:fi(?:-(qa|si)1)?\.unibet\.com|www\.kolikkopelit\.com|fi(?:-qa1|-si1)?\.mariacasino\.com|fi(?:-qa1|-si1)?\.bingo\.com)|www\-(qa1|si1)?\.casinohuone\.com/i,
            step: "eauth screen"
          },
          /* tupas implementation */
          criipto: {
            regex: /^criipto|manual$/i,
            host: /(?:unibet|mariacasino)\.dk/i,
            step: "eauth screen"
          },
          /* nemid mitid implementation */
          bankid: {
            regex: /^bankid$/i,
            host: /(?:unibet\.se|se(?:-qa1|-si1)?\.bingo\.com|www(?:-qa1|-si1)?\.mariacasino\.se|www(?:-qa1|-si1)?\.storspelare\.se)/i,
            step: "eauth screen"
          } /* bankid implementation */
        };
        // Find the matching registration method
        let matchedMethod = null;
        for (const method in registrationMethods) {
          const {
            regex,
            host
          } = registrationMethods[method];
          if (regex.test(data.registration_method) && host.test(location.host)) {
            matchedMethod = method;
            break;
          }
        }

        // Perform the server call if a matching method is found
        if (matchedMethod) {
          const {
            step
          } = registrationMethods[matchedMethod];
          registration_steps_server_call(data, step, matchedMethod);
        }
      }
      function welcomeOfferInteraction(eventName, data) {
        if (data.offerStatus == "" && data.offerSkipped == false) {
          data.offerStatus = "selected";
        }
        window.__welcome_offer_data = data.offerId + "~" + data.offerName + "~" + data.offerStatus + "~" + data.offerSkipped;
        try {
          if (data !== null && data !== void 0 && data.afterRegistration) {
            const checkOfferAccepted = data.offerSkipped === false;
            const offerType = checkOfferAccepted ? 'welcome offer accepted' : 'welcome offer declined';
            let schema_to_send = {
              event: {
                schema: getSnowplowSchemaURI("registration"),
                data: {
                  type: offerType,
                  method: "manual",
                  additionalDetails: null
                }
              }
            };
            //let schema_to_send = {
            //event: regSchema,
            if (checkOfferAccepted === true) {
              schema_to_send.context = schema_to_send.context || [];
              schema_to_send.context.push({
                schema: getSnowplowSchemaURI("offer"),
                data: {
                  "offerId": parseInt(data.offerId),
                  "name": data.offerName || "",
                  "accepted": checkOfferAccepted
                }
              });
            }
            //} 
            fireSnowplowEvent(schema_to_send);
          }
        } catch (e) {}
      }
      //registration steps
      function registrationSteps(eventName, data) {
        window._registrations_steps_fired = 1;
        registration_steps_server_call(data, "", "");

        //registration additional details to be included with the registration welcome offer screen
        if (data.currentStep === 'welcome offer screen') {
          let additionalDetails = data.additional_details;
          let schema_to_send = {
            event: {
              schema: getSnowplowSchemaURI('registration'),
              data: {
                type: data.currentStep,
                method: 'manual',
                additionalDetails: additionalDetails
              }
            }
          };
          fireSnowplowEvent(schema_to_send);
        }
      }
      //registration success
      function registrationSuccess(data) {
        let user_id = data.userId || "";
        let numericalUserId = Number(user_id);
        let welcome_offerId = null;
        let welcome_offerName = "";
        let welcome_offer_accepted = false;
        let communicationSelected = "";
        let communication_optin = false;
        let reg_method = data.authType || "";
        /* for unibet eu of idin registration platform */
        if (typeof data.registration_method !== "undefined" && data.registration_method !== null) {
          reg_method = data.registration_method;
        }
        if (typeof data.registrationType !== "undefined" && data.registrationType !== null) {
          reg_method = data.registrationType;
        }
        try {
          reg_method = /criipto/i.test(reg_method) ? "nemid_mitid" : reg_method;
        } catch (err) {}
        if (typeof data.offerId !== "undefined" && data.offerId !== "" && data.offerId !== null) {
          welcome_offerName = data.offerName || "";
          welcome_offerId = data.offerId;
          data.promoCode || "";
          if (/false/i.test(data.offerSkipped)) {
            welcome_offer_accepted = true;
          }
        }
        if (typeof data.communicationSelected !== "undefined" && data.communicationSelected !== null) {
          communicationSelected = "nothing selected";
          if (data.communicationSelected.constructor === Array) {
            communicationSelected = data.communicationSelected.join("~");
            communication_optin = true;
          }
        } else if (typeof data.communicationSelected !== "undefined" && (data.communicationSelected === null || data.communicationSelected === "")) {
          communicationSelected = "nothing selected";
        }
        if (typeof data.communication_optin !== "undefined" && /true/i.test(data.communication_optin)) {
          communication_optin = data.communication_optin;
        }
        window.snowplow('clearGlobalContexts');
        let schema_to_send = {
          event: {
            schema: getSnowplowSchemaURI("registration"),
            data: {
              type: 'success',
              method: reg_method || "manual",
              additionalDetails: null
            }
          },
          context: [{
            schema: getSnowplowSchemaURI("registrationComms"),
            data: {
              "communicationOptin": communication_optin,
              "communicationSelected": (communicationSelected || "").split("~")
            }
          }, {
            schema: getSnowplowSchemaURI("customer"),
            data: {
              "id": numericalUserId,
              "sessionId": sessionId || '',
              "isLoggedIn": (user_id || 0) > 0
            }
          }, {
            schema: getSnowplowSchemaURI("genericInteraction"),
            data: {
              "type": 'temp-app-reg-debug',
              "value": window.location.href.substring(0, 200),
              "additionalInfo": market
            }
          }, {
            schema: getSnowplowSchemaURI('login'),
            data: {
              "type": "success",
              // appeared, CTAClicked, closed, success, error
              "method": "registration",
              "ctaClicked": "registration",
              "widget_name": "registration",
              "is_first_login": true
            }
          }]
        };
        if (typeof welcome_offerId !== "undefined" && welcome_offerId !== "" && welcome_offerId != null) {
          schema_to_send.context.push({
            schema: getSnowplowSchemaURI("offer"),
            data: {
              "offerId": parseInt(welcome_offerId),
              "name": welcome_offerName || "",
              "accepted": welcome_offer_accepted
            }
          });
        }
        try {
          fireSnowplowEvent(schema_to_send);
        } catch (e) {}
      }
      function registrationFallback(eventName, data) {
        if (data.is_error === true) {
          var sanited_search = window.location.search.replace(/([^&?\/=]*)=/gi, x => x.toLowerCase());
          var params_obj = new URLSearchParams(sanited_search);
          var error_code = params_obj.get("error") || "";
          error_code = data.errorCode || error_code;
          let schema_to_send = {
            event: {
              schema: getSnowplowSchemaURI("registration"),
              data: {
                type: 'error',
                method: data.registration_method || "manual"
              }
            },
            context: [{
              schema: getSnowplowSchemaURI("error"),
              data: {
                "type": "registration error",
                "code": error_code,
                "product": "registration",
                "message": data.errorMessage || "error message unaivalable"
              }
            }]
          };
          fireSnowplowEvent(schema_to_send);
        } else {
          let step = "eauth last step";
          let method = data.registration_method;
          registration_steps_server_call(data, step, method);
        }
      }

      /* *** registration functions end *** */

      function registrationWaiting$1() {
        var _window, _window$location, _window2, _window2$location;
        if (/register|registration|sign-?up/i.test((_window = window) === null || _window === void 0 ? void 0 : (_window$location = _window.location) === null || _window$location === void 0 ? void 0 : _window$location.pathname) || /www(-(qa1|si1|pt1))?\.ottocasino\.se/i.test((_window2 = window) === null || _window2 === void 0 ? void 0 : (_window2$location = _window2.location) === null || _window2$location === void 0 ? void 0 : _window2$location.hostname)) {
          const inputEventHandler = function (evt) {
            if (typeof window._activateTrackingSnowplowRegistrationIntent_miniAppFired === "undefined") {
              if (/^(firstName|lastName|email|password|dropdown-day|dropdown-month|dropdown-year|gender-drop-down)-input-field$/i.test(evt.target.dataset.testName)) {
                window._activateTrackingSnowplowRegistrationIntent_miniAppFired = true;
                help_fire_snowplow('intent', window._registration_method || "manual", null);
                document.removeEventListener('input', inputEventHandler);
              }
            }
          };
          document.addEventListener('input', inputEventHandler);
          analyticsHelpers.waitForElm('[data-test-name="welcome-bonus-mini-app-container"]').then(elem => {
            help_fire_snowplow('welcome offer screen', null, null);
          });
          analyticsHelpers.waitForElm('[data-test-name="country-selector-page-container"]').then(elem => {
            help_fire_snowplow('select country', null, null);
          });
          analyticsHelpers.waitForElm('[id="itsmeButton"]').then(elem => {
            help_fire_snowplow("eauth screen", 'itsme', null);
          });
          analyticsHelpers.waitForElm('[data-test-name="itsme-registration-option"]').then(elem => {
            help_fire_snowplow("eauth screen", 'itsme', null);
          });
        }
      }
      function snowplow_click_on_nl_popup_cta() {
        jQuery(document).on("click", '[data-test-name="age-verification-modal"] button', function (evt) {
          if (typeof window._reg_popup_fired_snowplow_event !== "undefined") return false;
          window._reg_popup_fired_snowplow_event = false;
          let schema_to_send = {
            event: {
              schema: getSnowplowSchemaURI("popupMessage"),
              data: {
                "type": "ctaClicked",
                "activityName": "nl reg age verification",
                "ctaName": "confirm",
                "additionalInfo": null // needs to be revised
              }
            }
          };
          fireSnowplowEvent(schema_to_send);
        });
      }
      function snowplowCheckjQuery() {
        // Flag readyState: code executes faster before the page is fully loaded. Artifically delay applying tracking to make sure page is ready.
        if (typeof jQuery !== 'undefined' && typeof $ !== 'undefined' && document.readyState === 'complete') {
          snowplow_click_on_nl_popup_cta();
        } else setTimeout(snowplowCheckjQuery, 250);
      }

      var registrationEvents$1 = /*#__PURE__*/Object.freeze({
        __proto__: null,
        help_fire_snowplow: help_fire_snowplow,
        registrationEvents: registrationEvents,
        registrationWaiting: registrationWaiting$1,
        snowplowCheckjQuery: snowplowCheckjQuery
      });

      function setWidgetData(data) {
        let deep_copy_data = JSON.parse(JSON.stringify(data));
        let webAn = JSON.parse(window.sessionStorage.webAnalytics || '{}');
        if ((deep_copy_data === null || deep_copy_data === void 0 ? void 0 : deep_copy_data.widgetName) == 'QuickAccess') {
          let widgetURL = deep_copy_data.widget_element_name.split('?')[0];
          let widgetURLClean = widgetURL.split('/betting/sports/filter/');
          let widgetElementName = widgetURLClean[widgetURLClean.length - 1].replace(/((all\/all){1,})/gi, '').replace(/((\/all\/)?(matches|competitions))/gi, '').replace(/^\/{1,}/, '').replace(/\/{1,}$/, '');
          if (widgetElementName.includes('world_cup__w_')) widgetElementName = 'world cup women';
          if (widgetElementName.includes('~')) {
            widgetElementName = widgetElementName.split('~')[0];
          }
          if (widgetElementName == 'matches') {
            widgetElementName = widgetURLClean[widgetURLClean.length - 3];
          }
          if (widgetElementName == 'starting-soon') {
            widgetElementName = 'upcoming';
          }
          if (widgetElementName == 'unibet_featured') {
            widgetElementName = 'odds boosts';
          }
          if (widgetElementName == 'top50') {
            widgetElementName = 'top picks';
          }
          if (widgetElementName.includes('live-roulette')) {
            widgetElementName = 'live roulette';
          }
          deep_copy_data.widget_element_name = widgetElementName;
        }
        webAn['spdWidgetData'] = deep_copy_data;
        window.sessionStorage.webAnalytics = JSON.stringify(webAn);
        //window._sportsbook_widget = value;
      }

      //done
      function registrationWaiting() {
        var _window, _window$location, _window2, _window2$location;
        const {
          jurisdiction
        } = useDataLayer();
        if (/register|registration|sign-?up/i.test((_window = window) === null || _window === void 0 ? void 0 : (_window$location = _window.location) === null || _window$location === void 0 ? void 0 : _window$location.pathname) || /www(-(qa1|si1|pt1))?\.ottocasino\.se/i.test((_window2 = window) === null || _window2 === void 0 ? void 0 : (_window2$location = _window2.location) === null || _window2$location === void 0 ? void 0 : _window2$location.hostname)) {
          const inputEventHandler = function (evt) {
            if (typeof window._activateTrackingSnowplowRegistrationIntent_miniAppFired === "undefined") {
              if (/^(firstName|lastName|email|password|dropdown-day|dropdown-month|dropdown-year|gender-drop-down)-input-field$/i.test(evt.target.dataset.testName)) {
                window._activateTrackingSnowplowRegistrationIntent_miniAppFired = true;
                help_fire_snowplow('intent', window._registration_method || "manual", null);
                document.removeEventListener('input', inputEventHandler);
              }
            }
          };
          document.addEventListener('input', inputEventHandler);
          analyticsHelpers.waitForElm('[data-test-name="welcome-bonus-mini-app-container"]').then(elem => {
            help_fire_snowplow('welcome offer screen', null, null);
          });
          analyticsHelpers.waitForElm('[data-test-name="country-selector-page-container"]').then(elem => {
            help_fire_snowplow('select country', null, null);
          });
          analyticsHelpers.waitForElm('[id="itsmeButton"]').then(elem => {
            help_fire_snowplow("eauth screen", 'itsme', null);
          });
          analyticsHelpers.waitForElm('[data-test-name="itsme-registration-option"]').then(elem => {
            help_fire_snowplow("eauth screen", 'itsme', null);
          });
          if (/unibet.nl/i.test(location.hostname)) {
            analyticsHelpers.waitForElm('[data-test-name="age-verification-modal"]').then(elem => {
              let schema_to_send = {
                event: {
                  schema: getSnowplowSchemaURI("popupMessage"),
                  data: {
                    "type": "appeared",
                    "activityName": "nl reg age verification",
                    "ctaName": null,
                    "additionalInfo": null // needs to be revised
                  }
                }
              };
              fireSnowplowEvent(schema_to_send);
            });
          }
          if (/se/i.test(jurisdiction)) {
            analyticsHelpers.waitForElm('[data-test-name="start_bankID_button"]').then(elem => {
              elem.addEventListener('click', evt => {
                help_fire_snowplow('eauth start', 'bankid', null);
              });
            });
            analyticsHelpers.waitForElm('[data-test-name="start_bankID_on_another_device_button"]').then(elem => {
              elem.addEventListener('click', evt => {
                help_fire_snowplow('eauth start', 'bankid', null);
              });
            });
          }
          /* multi-page-registration-form-908099 old way */
          /* data-test-name="welcome-bonus-mini-app-container" */
          /* data-test-name="country-selector-page-container" unibet.com */
          analyticsHelpers.waitForElm("[id*=multi-page-registration-form]").then(elem => {
            window.addEventListener("hashchange", function (evt) {
              let regStep = null;
              if (/registrationStep:0/i.test(window.location.hash)) {
                regStep = "step 1";
              } else if (/registrationStep:1/i.test(window.location.hash)) {
                regStep = "step 2";
              } else if (/registrationStep:2/i.test(window.location.hash)) {
                regStep = "step 3";
              } else if (/registrationStep:3/i.test(window.location.hash)) {
                regStep = "step 4";
              }
              if (regStep) help_fire_snowplow(regStep, "manual", null);
            }, false);
            setTimeout(() => {
              let step = "step 1";
              let method = "password";
              if (document.querySelector("[id*=bankIdAuthentication]")) {
                step = "eauth screen";
                method = "bankid";
              }
              help_fire_snowplow(step, method, null);
            }, 500);
          });
        }
      }

      //logToSplunk is our main error handling function
      function logToSplunk$1(error, type, payload, functionName) {
        var _error$stack;
        if (typeof window !== 'object') return;
        if (analyticsHelpers.shouldLog()) {
          console.log('ADC: Splunk error:');
          console.log(error + "~" + type + "~" + payload + "~" + functionName);
        }
        const {
          brand,
          deviceGroup,
          jurisdiction,
          locale
        } = getSitedefinition();
        const data = {
          brand,
          jurisdiction,
          client_metadata: {
            deviceGroup,
            locale,
            moduleId: 'kwp-analytics'
          },
          events: [{
            data: {
              error: error.message,
              stack: (_error$stack = error.stack) === null || _error$stack === void 0 ? void 0 : _error$stack.split('\n').slice(0, 5).join('\n'),
              traceId: 'sendAnalyticsEventError',
              url: window.location.href,
              event: type,
              payload: payload,
              functionName: functionName
            },
            level: 'ERROR',
            timestamp: Date.now()
          }]
        };
        if ('sendBeacon' in window.navigator) {
          window.navigator.sendBeacon('/eum-collector/events', JSON.stringify(data));
        } else {
          console.error('[kwp-analytics]', data);
        }
      }

      //test3
      //safeSend used to prevent breaking the site. this function is called inside a try{}catch{} in sendAnalyticsEvent() which is our default function for the mini app
      function safeSendAnalyticsEvent(type, data, listener) {
        //do not track boabet sites
        if (/(www|hu)(-(qa1|si1|pt1|prod))?.boabet(-\d+)?\.com/i.test(window.location.hostname)) {
          return;
        }
        //event dispatch - this is required for automated testing. We send the event to the dtmEventTarget element, which what we previously used to trigger events in Tealium. 
        if (!listener) {
          var elem = document.getElementById('dtmEventTarget');
          var event = new CustomEvent(type, {
            detail: data
          });
          elem.dispatchEvent(event);
        }
        try {
          //handler for devtools journey tracker
          if (analyticsHelpers.storageManagement._getStorage("sessionStorage", "analytics-journey-tracker")) {
            if (data.detail) {
              data = data.detail;
              data.detail = undefined;
            }
            let payload = {
              eventName: type,
              data: data
            };
            try {
              analyticsHelpers.storageManagement._setStorage('sessionStorage', 'analytics-dev-web-event', payload);
            } catch (e) {
              console.log("ADC, cant set storage for analytics-dev-web-event", e);
            }
          }
        } catch (error) {
          logToSplunk$1(error, type, data, 'sendAnalyticsEvent');
        }
        //console logged for test envs
        if (analyticsHelpers.shouldLog()) {
          console.log('ADC: ' + type, data);
        }
        if (/unibet\.be/i.test(window.location.hostname)) {
          analyticsHelpers.belgiumClientId();
        }
        /*----Snowplow Events Start----*/
        if (type.toLowerCase() == 'pageview') {
          if (!/play/.test(window.location.pathname) && analyticsHelpers.storageManagement._getStorage("sessionStorage", "gameOpened")) {
            let schema_to_send = {
              event: {
                schema: getSnowplowSchemaURI("casinoInteraction"),
                data: {
                  type: "menu interaction",
                  menuName: "navigation_close_game"
                }
              }
            };
            closeGame('navigation', schema_to_send);
          }
          if (window.location.pathname !== "/betting/odds" && window.location.pathname !== "/racing" && !window.location.pathname.includes("/help")) {
            firePageview();
          }
          registrationWaiting();
          setDefaultCategoryFilter();
          if (window.location.pathname.includes('/live-casino') || window.location.pathname.includes('/livecasino')) {
            analyticsHelpers.storageManagement._setStorage("sessionStorage", "pageurl", window.location.pathname);
          }
        } else {
          const getEventFileAndFunction = async (type, data) => {
            if (/registration/i.test(type) || data && data.errorType === 'registrationError') {
              return {
                file: await Promise.resolve().then(function () { return registrationEvents$1; }),
                fn: 'registrationEvents',
                args: [type, data]
              };
            } else if (type === 'post_login_interaction') {
              return {
                file: await module.import('./postLoginInteraction-93bf3312.js'),
                fn: 'postLoginInteraction',
                args: [data]
              };
            } else if (/login/i.test(type) || type === 'passwordResetSubmit') {
              return {
                file: await module.import('./loginEvents-b0c48cf8.js'),
                fn: 'loginEvents',
                args: [type, data]
              };
            } else if (/gameNavigation/i.test(type)) {
              return {
                file: await Promise.resolve().then(function () { return casinoLobbyInteractions; }),
                fn: 'gameNavigation',
                args: [data]
              };
            } else if (/gamingWidgetInteraction/i.test(type)) {
              return {
                file: await Promise.resolve().then(function () { return casinoLobbyInteractions; }),
                fn: 'gamingWidgetInteraction',
                args: [data]
              };
            } else if (/pokerInteraction/i.test(type)) {
              return {
                file: await module.import('./pokerPageInteractions-134a5634.js'),
                fn: 'pokerInteraction',
                args: [data]
              };
            } else if (/pokerSearchModule/i.test(type)) {
              return {
                file: await module.import('./pokerPageInteractions-134a5634.js'),
                fn: 'pokerSearchModule',
                args: [data]
              };
            } else if (/selfassessment/i.test(type)) {
              return {
                file: await module.import('./selfTestInteraction-4ed198af.js'),
                fn: 'selfTestCompleteSnowplow',
                args: [data]
              };
            } else if (/controls_and_limits/i.test(type)) {
              return {
                file: await module.import('./controlsAndLimits-4e59bffa.js'),
                fn: 'controlsAndLimitsEvents',
                args: [data]
              };
            } else if (/^(siteModal|modal)$/i.test(type)) {
              return {
                file: await module.import('./popupMessageInteractions-55014c7f.js'),
                fn: 'modalInteraction',
                args: [data, false]
              };
            } else if (/^(personalDetailsCTAClicked|popupmessage)$/i.test(type)) {
              return {
                file: await module.import('./popupMessageInteractions-55014c7f.js'),
                fn: 'popupmessageInteraction',
                args: [type, data]
              };
            } else if (/gamelaunch/i.test(type)) {
              return {
                file: await Promise.resolve().then(function () { return casinoInGameInteractions; }),
                fn: 'gameLaunchEvent',
                args: [data]
              };
            } else if (/gameSearchModule/i.test(type)) {
              return {
                file: await Promise.resolve().then(function () { return casinoLobbyInteractions; }),
                fn: 'gameSearchModule',
                args: [data]
              };
            } else if (/gameMenuInteraction/i.test(type) || /globalJackpotInteraction/i.test(type)) {
              if (/globalJackpotInteraction/i.test(type)) {
                data.type = "jackpot all games";
              }
              return {
                file: await Promise.resolve().then(function () { return casinoInGameInteractions; }),
                fn: 'gameMenuInteraction',
                args: [data]
              };
            } else if (/nextGameInteraction/i.test(type)) {
              return {
                file: await Promise.resolve().then(function () { return casinoInGameInteractions; }),
                fn: 'nextGameInteraction',
                args: [data]
              };
            } else if (/kmf_verification_event/i.test(type)) {
              return {
                file: await module.import('./verificationInteractions-cd85b8d2.js'),
                fn: 'verificationInteration',
                args: [data]
              };
            } else if (/^(openMsg|msgList|deleteMsg)$/i.test(type)) {
              return {
                file: await module.import('./messageCenterInteraction-65999910.js'),
                fn: 'handlMessageCenterInteraction',
                args: [type, data]
              };
            } else if (/bonus/.test(type)) {
              return {
                file: await module.import('./bonusInteraction-37b65c05.js'),
                fn: 'bonusEvents',
                args: [type, data]
              };
            } else if (/tournament/.test(type)) {
              return {
                file: await module.import('./tournamentInteractions-ccd1e273.js'),
                fn: 'tournamentHandler',
                args: [type, data]
              };
            } else if (/promo/i.test(type)) {
              return {
                file: await module.import('./promotionInteractions-2ca1b901.js'),
                fn: 'promotionHandler',
                args: [type, data]
              };
            } else if (/^(sportbookEvents|racingInteraction)$/i.test(type)) {
              if (/unibet/i.test(window.location.hostname) && /\/racing/i.test(window.location.pathname)) {
                return {
                  file: await module.import('./racingEvents-62c2c77d.js'),
                  fn: 'racingHandler',
                  args: [type, data]
                };
              } else {
                return {
                  file: await module.import('./sportsbookInteractions-64d40933.js'),
                  fn: 'sportsbookEvents',
                  args: [type, data]
                };
              }
            } else if (type === 'kspEvent') {
              return {
                file: await module.import('./kspEvents-dab1cbc1.js'),
                fn: 'kspEvents',
                args: [type, data]
              };
            } else if (/experimentActivated/i.test(type)) {
              return {
                file: await module.import('./experiment-7a4e70d0.js'),
                fn: 'experimentHandler',
                args: [type, data]
              };
            } else if (type === 'cashbackInteraction') {
              return {
                file: await module.import('./cashbackInteraction-8ef2d1a2.js'),
                fn: 'cashbackHandler',
                args: [type, data]
              };
            } else if (/msg/g.test(type)) {
              return {
                file: await module.import('./messageCenterInteraction-65999910.js'),
                fn: 'handlMessageCenterInteraction',
                args: [type, data]
              };
            } else if (/genericInteraction/.test(type)) {
              return {
                file: await module.import('./genericInteraction-4c5c9c9c.js'),
                fn: 'genericInteraction',
                args: [data]
              };
            } else if (/channel_verification_interaction/i.test(type)) {
              return {
                file: await module.import('./verificationInteractions-cd85b8d2.js'),
                fn: 'channelVerificationInteraction',
                args: [type, data]
              };
            } else if (/paymentUserEvent/i.test(type)) {
              return {
                file: await module.import('./paymentUserEvent-e50dc800.js'),
                fn: 'paymentUserEvent',
                args: [type, data]
              };
            } else if (/installationInteraction/i.test(type)) {
              return {
                file: await module.import('./installationInteraction-b76ad2ae.js'),
                fn: 'installationInteraction',
                args: [type, data]
              };
            } else if (/genericBannerInteraction/i.test(type)) {
              return {
                file: await module.import('./genericBannerInteraction-46c3e944.js'),
                fn: 'genericBannerInteraction',
                args: [type, data]
              };
            } else if (/offlineInteraction/i.test(type)) {
              return {
                file: await module.import('./offlineInteractions-ae16d2ad.js'),
                fn: 'offlineInteraction',
                args: [type, data]
              };
            } else if (/notificationInteraction/i.test(type)) {
              return {
                file: await module.import('./notificationInteraction-a7056954.js'),
                fn: 'notificationInteraction',
                args: [data]
              };
            } else if (/help_?centre_?interaction/i.test(type)) {
              return {
                file: await module.import('./help_centre_interaction-44132439.js'),
                fn: 'help_centre_interaction',
                args: [type, data]
              };
            } else if (/deposit/i.test(type)) {
              return {
                file: await module.import('./depositEvents-e730dbcc.js'),
                fn: 'handleDepositEvent',
                args: [data]
              };
            } else if (/hamburgerMenuClick/i.test(type)) {
              return {
                file: await module.import('./hamburgerMenuInteraction-a8901a76.js'),
                fn: 'hamburgerMenuClick',
                args: [data]
              };
            }
            // Default: no match found
            return null;
          };
          const handlingEvent = async (type, data) => {
            const eventInfo = await getEventFileAndFunction(type, data);
            if (!eventInfo) return;
            const eventModule = await eventInfo.file;
            if (!eventModule) return;
            if (eventInfo.fn && typeof eventModule[eventInfo.fn] === 'function') {
              eventModule[eventInfo.fn](...eventInfo.args);
            }
          };
          handlingEvent(type, data).catch(err => {
            logToSplunk$1(err, type, data, 'handlingEvent');
          });
        }

        //Marketing events
        const {
          isApp
        } = useDataLayer();
        if (isApp) {
          return;
        } else {
          //only some events are marketing events, so we need to check if the event is in the marketingEvents array
          if (marketingEvents().includes(type)) {
            marketingHandler(type, data);
          }
        }
      }
      //sendAnalyticsEvent is called by other miniApps and is our default function for the mini app
      function sendAnalyticsEvent(type) {
        let data = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : {};
        let listener = arguments.length > 2 && arguments[2] !== undefined ? arguments[2] : false;
        //try{}catch{} is used to prevent the site from breaking if an error occurs
        try {
          if (!(/\/betting\/odds\//i.test(document.location.pathname) && type == 'pageView')) {
            safeSendAnalyticsEvent(type, data, listener);
          }
        } catch (error) {
          logToSplunk$1(error, type, data, 'sendAnalyticsEvent');
        }
      }

      //Make TypeScript classes available globally for console usage
      if (typeof window !== 'undefined') {
        window.RegistrationSession = RegistrationSession;
        window.VerificationEvent = VerificationEvent;
        window.UniversalAnalyticsSender = UniversalAnalyticsSender;
        window.TournamentView = TournamentView;
        window.TournamentOptIn = TournamentOptIn;
        window.ControlsAndLimitEvent = ControlsAndLimitEvent;
        window.LoginEvent = LoginEvent;
        //window.DepositDataObject = DepositDataObject;
        // Also expose the main analytics function
        window.sendAnalyticsEvent = sendAnalyticsEvent;
      }

      eventList();

      // Recursive initializer for field default values
      const initializeFieldValue = f => {
        if (f.type === 'object') {
          if (f.defaultValue && typeof f.defaultValue === 'object' && !Array.isArray(f.defaultValue)) {
            const o = {};
            for (const k in f.defaultValue) {
              const nested = f.defaultValue[k];
              if ((nested === null || nested === void 0 ? void 0 : nested.defaultValue) !== undefined) o[k] = initializeFieldValue(nested);
            }
            return o;
          }
          // Build from f.fields when schema has no defaultValue (e.g. widget_data)
          if (Array.isArray(f.fields) && f.fields.length > 0) {
            return Object.fromEntries(f.fields.map(sf => {
              var _sf$name;
              return [(_sf$name = sf.name) !== null && _sf$name !== void 0 ? _sf$name : sf.label, initializeFieldValue(sf)];
            }));
          }
          return {};
        }
        if (f.type === 'array') {
          if (Array.isArray(f.defaultValue)) {
            return f.defaultValue.map(item => item && typeof item === 'object' && !Array.isArray(item) ? Object.fromEntries(Object.entries(item).filter(_ref => {
              let [_, v] = _ref;
              return (v === null || v === void 0 ? void 0 : v.defaultValue) !== undefined;
            }).map(_ref2 => {
              let [k, nested] = _ref2;
              return [k, initializeFieldValue(nested)];
            })) : item);
          }
          // Build one item from f.items when schema has no defaultValue
          if (Array.isArray(f.items) && f.items.length > 0) {
            return [Object.fromEntries(f.items.map(sf => {
              var _sf$name2;
              return [(_sf$name2 = sf.name) !== null && _sf$name2 !== void 0 ? _sf$name2 : sf.label, initializeFieldValue(sf)];
            }))];
          }
          return [];
        }
        return f.defaultValue;
      };
      const renderCodeBlock$1 = (payload, eventString) => /*#__PURE__*/jsxs("div", {
        style: {
          position: 'relative'
        },
        children: [/*#__PURE__*/jsx("pre", {
          style: {
            margin: 0,
            padding: '12px 40px 12px 12px',
            background: 'rgba(150, 150, 150, 0.1)',
            borderRadius: 6,
            fontFamily: 'monospace',
            fontSize: 12,
            whiteSpace: 'pre',
            overflow: 'auto'
          },
          children: eventString(payload)
        }), /*#__PURE__*/jsx(Button, {
          type: "text",
          size: "small",
          icon: /*#__PURE__*/jsx(CopyOutlined, {}),
          onClick: () => {
            navigator.clipboard.writeText(eventString(payload));
            message.success('Copied!');
          },
          style: {
            position: 'absolute',
            top: 8,
            right: 8
          },
          "aria-label": "Copy code"
        })]
      });
      const AnalyticsTriggerEvents = () => {
        const [selectedEvent, setSelectedEvent] = useState(null);
        const [dropdownOpen, setDropdownOpen] = useState(false);
        const [sizes, setSizes] = useState(['30%', '70%']);
        const [enabled] = useState(true);
        const [fieldValues, setFieldValues] = useState({});
        const [enabledFields, setEnabledFields] = useState({});
        const [lastAppPayload, setLastAppPayload] = useState(null);
        const [appPayloadReady, setAppPayloadReady] = useState(false);
        const appPayloadFlushRef = useRef(false);
        const selectedFields = useMemo(() => {
          if (!(selectedEvent !== null && selectedEvent !== void 0 && selectedEvent.fields)) return [];
          return Array.isArray(selectedEvent.fields) ? selectedEvent.fields : [];
        }, [selectedEvent]);
        const selectedCategoryLabel = useMemo(() => {
          if (!selectedEvent) return '';
          for (const cat of eventCategories()) {
            if (cat.events.some(e => e.eventName === selectedEvent.eventName)) {
              return cat.label;
            }
          }
          return '';
        }, [selectedEvent]);
        useEffect(() => {
          const v = {};
          const en = {};
          for (const f of selectedFields) {
            v[f.name] = initializeFieldValue(f);
            en[f.name] = !(f.type === 'object' || f.type === 'array');
          }
          setFieldValues(v);
          setEnabledFields(en);
        }, [selectedFields]);
        const handleFieldChange = useCallback((name, value) => {
          setFieldValues(prev => _objectSpread2(_objectSpread2({}, prev), {}, {
            [name]: value
          }));
        }, []);
        const toggleFieldEnabled = useCallback(name => {
          setEnabledFields(prev => _objectSpread2(_objectSpread2({}, prev), {}, {
            [name]: !prev[name]
          }));
        }, []);
        const currentPayload = useMemo(() => {
          var _selectedEvent$eventN;
          return {
            eventName: (_selectedEvent$eventN = selectedEvent === null || selectedEvent === void 0 ? void 0 : selectedEvent.eventName) !== null && _selectedEvent$eventN !== void 0 ? _selectedEvent$eventN : '',
            data: Object.fromEntries(Object.entries(fieldValues).filter(_ref3 => {
              let [k] = _ref3;
              return enabledFields[k] !== false;
            }))
          };
        }, [selectedEvent, fieldValues, enabledFields]);

        // Web tab: display only what's in the form (plain copy, no runtime refs / circular data)
        const webDisplayPayload = useMemo(() => {
          try {
            return JSON.parse(JSON.stringify(currentPayload));
          } catch (_unused) {
            return {
              eventName: currentPayload.eventName,
              data: {}
            };
          }
        }, [currentPayload]);

        /**
         * App tab shows the same `schema_to_send` written in fireSnowplowEvent (helpers.tsx):
         * sessionStorage `analytics-dev-app-event` + CustomEvent `analytics-dev-tracker-event` detail.
         * Event routing uses dynamic import, so capture may run after a microtask — we flush from
         * the event detail first, then fall back to storage, then a delayed read.
         */
        const flushCapturedAppPayload = useCallback(source => {
          if (appPayloadFlushRef.current) return;
          const fromDetail = source && typeof source === 'object' && source !== null && 'event' in source ? source : null;
          const fromStorage = analyticsHelpers.storageManagement._getStorage('sessionStorage', 'analytics-dev-app-event');
          const payload = fromDetail !== null && fromDetail !== void 0 ? fromDetail : fromStorage;
          if (payload == null) {
            return;
          }
          appPayloadFlushRef.current = true;
          try {
            setLastAppPayload(JSON.parse(JSON.stringify(payload)));
          } catch (_unused2) {
            setLastAppPayload(payload);
          }
          setAppPayloadReady(true);
          analyticsHelpers.storageManagement._deleteStorage('sessionStorage', 'analytics-dev-app-event');
        }, []);
        const handleFireEvent = useCallback(() => {
          if (!currentPayload.eventName) return;
          appPayloadFlushRef.current = false;
          const onDevTracker = ev => {
            const ce = ev;
            flushCapturedAppPayload(ce.detail);
            document.removeEventListener('analytics-dev-tracker-event', onDevTracker);
          };
          analyticsHelpers.storageManagement._setStorage('sessionStorage', 'analytics-dev-event', true);
          document.addEventListener('analytics-dev-tracker-event', onDevTracker);
          sendAnalyticsEvent(currentPayload.eventName, currentPayload.data);
          // handlingEvent() awaits dynamic import before fireSnowplowEvent; microtasks run before this macrotask
          window.setTimeout(() => {
            flushCapturedAppPayload();
            document.removeEventListener('analytics-dev-tracker-event', onDevTracker);
          }, 0);
          // Slow network / chunk load: retry once
          window.setTimeout(() => {
            flushCapturedAppPayload();
            document.removeEventListener('analytics-dev-tracker-event', onDevTracker);
          }, 150);
        }, [currentPayload, flushCapturedAppPayload]);
        const eventString = payload => payload.eventName === 'kspEvent' ? `\nimport sendAnalyticsEvent from 'kwp-analytics'\n\ndata = {\n detail:${JSON.stringify(payload.data, null, 2)}\n}\n\nsendAnalyticsEvent('${payload.eventName}', data)` : `\nimport sendAnalyticsEvent from 'kwp-analytics'\n\ndata = ${JSON.stringify(payload.data, null, 2)}\n\nsendAnalyticsEvent('${payload.eventName}', data)`;
        const indentData = data => {
          const dataStr = JSON.stringify(data, null, 2);
          const dataLines = dataStr.split('\n');
          const indent = '      ';
          const closingIndent = '    ';
          const indentedData = dataLines.length === 1 ? dataLines[0] : dataLines.map(line => {
            const trimmed = line.trim();
            if (trimmed === '{') return trimmed;
            if (trimmed === '}') return closingIndent + trimmed;
            return indent + line;
          }).join('\n');
          return indentedData;
        };
        const appEventString = payload => {
          var _payload$event$schema, _payload$event, _payload$event$data, _payload$event2;
          const eventSchema = (_payload$event$schema = payload === null || payload === void 0 ? void 0 : (_payload$event = payload.event) === null || _payload$event === void 0 ? void 0 : _payload$event.schema) !== null && _payload$event$schema !== void 0 ? _payload$event$schema : '';
          const eventData = indentData((_payload$event$data = payload === null || payload === void 0 ? void 0 : (_payload$event2 = payload.event) === null || _payload$event2 === void 0 ? void 0 : _payload$event2.data) !== null && _payload$event$data !== void 0 ? _payload$event$data : {});
          try {
            var _payload$context;
            return `tracker.trackSelfDescribingEvent({\n  event: {\n    schema: '${eventSchema}',\n    data: ${eventData}\n  },\n  context: [\n${((_payload$context = payload === null || payload === void 0 ? void 0 : payload.context) !== null && _payload$context !== void 0 ? _payload$context : []).map(c => `    {\n      schema: '${c.schema}',\n      data: ${indentData(c.data)}\n    }`).join(',\n')}\n  ]\n})`;
          } catch (_unused3) {
            return `Fire an event to see the app payload here.`;
          }
        };
        const eventMenuItems = useMemo(() => eventCategories().map(cat => ({
          key: `cat-${cat.key}`,
          label: cat.label,
          children: cat.events.map(event => ({
            key: event.eventName,
            label: event.label,
            onClick: () => {
              setSelectedEvent(event);
              setDropdownOpen(false);
            }
          }))
        })), []);
        const appTabContent = (() => {
          if (!appPayloadReady || lastAppPayload == null) {
            return /*#__PURE__*/jsx(Typography.Text, {
              type: "secondary",
              children: "Fire an event to view the equivalent app payload."
            });
          }
          let code;
          try {
            code = appEventString(lastAppPayload);
          } catch (_unused4) {
            return /*#__PURE__*/jsx(Typography.Text, {
              type: "secondary",
              children: "Please try firing the event again."
            });
          }
          return /*#__PURE__*/jsxs("div", {
            style: {
              position: 'relative'
            },
            children: [/*#__PURE__*/jsx("pre", {
              style: {
                margin: 0,
                padding: '12px 40px 12px 12px',
                background: 'rgba(150, 150, 150, 0.1)',
                borderRadius: 6,
                fontFamily: 'monospace',
                fontSize: 12,
                whiteSpace: 'pre',
                overflow: 'auto'
              },
              children: code
            }), /*#__PURE__*/jsx(Button, {
              type: "text",
              size: "small",
              icon: /*#__PURE__*/jsx(CopyOutlined, {}),
              onClick: () => {
                navigator.clipboard.writeText(code);
                message.success('Copied!');
              },
              style: {
                position: 'absolute',
                top: 8,
                right: 8
              },
              "aria-label": "Copy code"
            })]
          });
        })();
        const tabItems = [{
          key: 'web',
          label: 'Web',
          icon: /*#__PURE__*/jsx(DesktopOutlined, {}),
          children: renderCodeBlock$1(webDisplayPayload, eventString)
        }, {
          key: 'app',
          label: 'App',
          icon: /*#__PURE__*/jsx(MobileOutlined, {}),
          children: appTabContent
        }];
        return /*#__PURE__*/jsx(Flex, {
          vertical: true,
          gap: "middle",
          children: /*#__PURE__*/jsxs(Splitter, {
            onResize: setSizes,
            children: [/*#__PURE__*/jsx(Splitter.Panel, {
              defaultSize: "40%",
              min: "30%",
              size: sizes[0],
              resizable: enabled,
              children: /*#__PURE__*/jsxs(Space, {
                direction: "vertical",
                size: "middle",
                style: {
                  display: 'flex',
                  width: '90%'
                },
                children: [/*#__PURE__*/jsx(Dropdown, {
                  menu: {
                    items: eventMenuItems
                  },
                  open: dropdownOpen,
                  onOpenChange: setDropdownOpen,
                  trigger: ['click'],
                  children: /*#__PURE__*/jsx(Button, {
                    onClick: e => e.preventDefault(),
                    icon: dropdownOpen ? /*#__PURE__*/jsx(DownOutlined, {}) : /*#__PURE__*/jsx(RightOutlined, {}),
                    iconPlacement: "end",
                    style: {
                      width: '100%'
                    },
                    children: selectedEvent ? selectedCategoryLabel ? `${selectedCategoryLabel} > ${selectedEvent.label}` : selectedEvent.label : 'Select Event'
                  })
                }), /*#__PURE__*/jsx(Button, {
                  disabled: !selectedEvent,
                  onClick: handleFireEvent,
                  icon: /*#__PURE__*/jsx(RocketOutlined, {}),
                  iconPlacement: "end",
                  style: {
                    width: '100%'
                  },
                  children: "Fire Event"
                }), selectedEvent ? /*#__PURE__*/jsxs(Space, {
                  direction: "vertical",
                  size: "middle",
                  style: {
                    width: '100%'
                  },
                  children: [/*#__PURE__*/jsx(Typography.Text, {
                    strong: true,
                    children: "Event Parameters"
                  }), /*#__PURE__*/jsx(PayloadFormAntd, {
                    fields: selectedFields,
                    fieldValues: fieldValues,
                    enabledFields: enabledFields,
                    onFieldChange: handleFieldChange,
                    onToggleFieldEnabled: toggleFieldEnabled
                  })]
                }) : /*#__PURE__*/jsx(Typography.Text, {
                  type: "secondary",
                  children: "Select an event to edit payload and fire."
                })]
              })
            }), /*#__PURE__*/jsxs(Splitter.Panel, {
              defaultSize: "60%",
              min: "40%",
              size: sizes[1],
              resizable: enabled,
              children: [/*#__PURE__*/jsx(Typography.Text, {
                strong: true,
                children: "Event Payloads"
              }), /*#__PURE__*/jsx(Tabs, {
                type: "card",
                items: tabItems
              })]
            })]
          })
        });
      };

      // Antd-based payload form (dropdowns, inputs, checkboxes, nested objects)

      function PayloadFormAntd(_ref4) {
        let {
          fields,
          fieldValues,
          enabledFields,
          onFieldChange,
          onToggleFieldEnabled
        } = _ref4;
        const renderField = function (field, value, onChange) {
          var _field$label, _ref6, _ref7;
          let depth = arguments.length > 3 && arguments[3] !== undefined ? arguments[3] : 0;
          const label = (_field$label = field.label) !== null && _field$label !== void 0 ? _field$label : field.name;
          const style = depth > 0 ? {
            marginLeft: depth * 16
          } : undefined;
          switch (field.type) {
            case 'select':
              {
                var _ref5, _field$options;
                const stringValue = String((_ref5 = value !== null && value !== void 0 ? value : field.defaultValue) !== null && _ref5 !== void 0 ? _ref5 : '');
                const options = (_field$options = field.options) !== null && _field$options !== void 0 ? _field$options : [];
                const valueMatchesOption = options.some(opt => String(opt) === stringValue);
                const isFreeform = !valueMatchesOption && stringValue !== '';
                const selectOptions = options.map(opt => ({
                  value: String(opt),
                  label: String(opt)
                }));
                selectOptions.push({
                  value: '__freeform__',
                  label: 'Freeform...'
                });
                if (isFreeform) {
                  selectOptions.unshift({
                    value: stringValue,
                    label: `Freeform (${stringValue})`
                  });
                }
                return /*#__PURE__*/jsx(Form.Item, {
                  label: label,
                  style: style,
                  children: /*#__PURE__*/jsxs(Space, {
                    direction: "vertical",
                    style: {
                      width: '100%'
                    },
                    children: [/*#__PURE__*/jsx(Select, {
                      style: {
                        width: '100%'
                      },
                      value: valueMatchesOption || isFreeform ? stringValue : '__freeform__',
                      options: selectOptions,
                      onChange: val => {
                        var _field$options2;
                        if (val === '__freeform__') onChange('');else if (val === 'null') onChange(null);else if (val === 'true') onChange(true);else if (val === 'false') onChange(false);else if ((_field$options2 = field.options) !== null && _field$options2 !== void 0 && _field$options2.some(o => typeof o === 'number') && !isNaN(Number(val))) onChange(Number(val));else onChange(val);
                      }
                    }), (stringValue === '' || !valueMatchesOption) && /*#__PURE__*/jsx(Input, {
                      placeholder: "Enter custom value",
                      value: value !== null && value !== void 0 ? value : '',
                      onChange: e => onChange(e.target.value)
                    })]
                  })
                }, field.name);
              }
            case 'text':
              return /*#__PURE__*/jsx(Form.Item, {
                label: label,
                style: style,
                children: /*#__PURE__*/jsx(Input, {
                  value: (_ref6 = value !== null && value !== void 0 ? value : field.defaultValue) !== null && _ref6 !== void 0 ? _ref6 : '',
                  onChange: e => onChange(e.target.value)
                })
              }, field.name);
            case 'number':
              return /*#__PURE__*/jsx(Form.Item, {
                label: label,
                style: style,
                children: /*#__PURE__*/jsx(InputNumber, {
                  style: {
                    width: '100%'
                  },
                  value: value !== null && value !== void 0 ? value : field.defaultValue,
                  onChange: v => onChange(v)
                })
              }, field.name);
            case 'boolean':
              return /*#__PURE__*/jsx(Form.Item, {
                style: style,
                children: /*#__PURE__*/jsx(Checkbox, {
                  checked: (_ref7 = value !== null && value !== void 0 ? value : field.defaultValue) !== null && _ref7 !== void 0 ? _ref7 : false,
                  onChange: e => onChange(e.target.checked),
                  children: label
                })
              }, field.name);
            case 'object':
              {
                const objectFields = Array.isArray(field.fields) ? field.fields : [];
                if (objectFields.length === 0) return null;
                const objValue = value !== null && value !== void 0 ? value : {};
                const headerContent = depth === 0 ? /*#__PURE__*/jsx("span", {
                  onClick: e => e.stopPropagation(),
                  children: /*#__PURE__*/jsx(Checkbox, {
                    checked: !!enabledFields[field.name],
                    onChange: () => onToggleFieldEnabled(field.name),
                    children: /*#__PURE__*/jsxs(Typography.Text, {
                      strong: true,
                      children: ["Include ", label]
                    })
                  })
                }) : label;
                return /*#__PURE__*/jsx(Collapse, {
                  style: style,
                  items: [{
                    key: field.name,
                    label: headerContent,
                    children: objectFields.map(f => {
                      var _f$name;
                      return /*#__PURE__*/jsx("div", {
                        children: renderField(f, objValue[(_f$name = f.name) !== null && _f$name !== void 0 ? _f$name : f.label], val => {
                          var _f$name2;
                          return onChange(_objectSpread2(_objectSpread2({}, objValue), {}, {
                            [(_f$name2 = f.name) !== null && _f$name2 !== void 0 ? _f$name2 : f.label]: val
                          }));
                        }, depth + 1)
                      }, f.name);
                    })
                  }]
                }, field.name);
              }
            case 'array':
              {
                let itemFields = [];
                if (Array.isArray(field.items) && field.items.length > 0) {
                  itemFields = field.items;
                } else if (Array.isArray(field.defaultValue) && field.defaultValue[0] && typeof field.defaultValue[0] === 'object') {
                  itemFields = Array.isArray(field.defaultValue[0].fields) ? field.defaultValue[0].fields : Object.keys(field.defaultValue[0]).map(k => _objectSpread2(_objectSpread2({}, field.defaultValue[0][k]), {}, {
                    name: k
                  }));
                }
                if (itemFields.length === 0) return null;
                const arrValue = Array.isArray(value) && value[0] ? value[0] : {};
                const arr = Array.isArray(value) ? [...value] : [{}];
                const arrayHeaderContent = depth === 0 ? /*#__PURE__*/jsx("span", {
                  onClick: e => e.stopPropagation(),
                  children: /*#__PURE__*/jsx(Checkbox, {
                    checked: !!enabledFields[field.name],
                    onChange: () => onToggleFieldEnabled(field.name),
                    children: /*#__PURE__*/jsxs(Typography.Text, {
                      strong: true,
                      children: ["Include ", label, " (first item)"]
                    })
                  })
                }) : `${label} (first item)`;
                return /*#__PURE__*/jsx(Collapse, {
                  style: style,
                  items: [{
                    key: field.name,
                    label: arrayHeaderContent,
                    children: itemFields.map(f => {
                      var _f$name3;
                      return /*#__PURE__*/jsx("div", {
                        children: renderField(f, arrValue[(_f$name3 = f.name) !== null && _f$name3 !== void 0 ? _f$name3 : f.label], val => {
                          var _f$name4;
                          arr[0] = _objectSpread2(_objectSpread2({}, arr[0] || {}), {}, {
                            [(_f$name4 = f.name) !== null && _f$name4 !== void 0 ? _f$name4 : f.label]: val
                          });
                          onChange(arr);
                        }, depth + 1)
                      }, f.name);
                    })
                  }]
                }, field.name);
              }
            default:
              return null;
          }
        };
        if (fields.length === 0) {
          return /*#__PURE__*/jsx(Typography.Text, {
            type: "secondary",
            children: "No parameters for this event."
          });
        }
        return /*#__PURE__*/jsx(Form, {
          layout: "vertical",
          size: "small",
          children: fields.map(field => /*#__PURE__*/jsx("div", {
            children: renderField(field, fieldValues[field.name], val => onFieldChange(field.name, val))
          }, field.name))
        });
      }

      const JOURNEY_TRACKER_KEY = 'analytics-journey-tracker';
      const DEV_EVENT_KEY = 'analytics-dev-event';
      const JOURNEY_EVENTS_KEY = 'analytics-journey-tracker-events';
      function readJourneyTrackerEnabledFromSession() {
        const v = analyticsHelpers.storageManagement._getStorage('sessionStorage', JOURNEY_TRACKER_KEY);
        return v === true || v === 'true';
      }
      function readJourneyEventsFromSession() {
        const raw = analyticsHelpers.storageManagement._getStorage('sessionStorage', JOURNEY_EVENTS_KEY);
        let list = [];
        if (raw == null) return [];
        if (Array.isArray(raw)) {
          list = raw;
        } else if (typeof raw === 'string') {
          try {
            const parsed = JSON.parse(raw);
            list = Array.isArray(parsed) ? parsed : [];
          } catch (_unused) {
            return [];
          }
        } else {
          return [];
        }
        // Newest first (persisted lists may be oldest-first from earlier versions)
        return [...list].sort((a, b) => b.at - a.at);
      }
      function writeJourneyEventsToSession(events) {
        analyticsHelpers.storageManagement._setStorage('sessionStorage', JOURNEY_EVENTS_KEY, events);
      }
      function clearJourneyEventsFromSession() {
        analyticsHelpers.storageManagement._deleteStorage('sessionStorage', JOURNEY_EVENTS_KEY);
      }
      const indentData = data => {
        const dataStr = JSON.stringify(data, null, 2);
        const dataLines = dataStr.split('\n');
        const indent = '      ';
        const closingIndent = '    ';
        const indentedData = dataLines.length === 1 ? dataLines[0] : dataLines.map(line => {
          const trimmed = line.trim();
          if (trimmed === '{') return trimmed;
          if (trimmed === '}') return closingIndent + trimmed;
          return indent + line;
        }).join('\n');
        return indentedData;
      };
      const eventString = payload => {
        if (payload === null || typeof payload === 'undefined') {
          return ``;
        } else {
          return `\nimport sendAnalyticsEvent from 'kwp-analytics'\n\ndata = ${JSON.stringify(payload.data, null, 2)}\n\nsendAnalyticsEvent('${payload.eventName}', data)`;
        }
      };
      const appEventString = payload => {
        var _payload$data, _schema, _payload$data2, _payload$data2$event, _data, _payload$data3, _payload$data3$event;
        const ctx = payload === null || payload === void 0 ? void 0 : (_payload$data = payload.data) === null || _payload$data === void 0 ? void 0 : _payload$data.context;
        const contextList = Array.isArray(ctx) ? ctx : [];
        const eventSchema = (_schema = payload === null || payload === void 0 ? void 0 : (_payload$data2 = payload.data) === null || _payload$data2 === void 0 ? void 0 : (_payload$data2$event = _payload$data2.event) === null || _payload$data2$event === void 0 ? void 0 : _payload$data2$event.schema) !== null && _schema !== void 0 ? _schema : '';
        const eventData = indentData((_data = payload === null || payload === void 0 ? void 0 : (_payload$data3 = payload.data) === null || _payload$data3 === void 0 ? void 0 : (_payload$data3$event = _payload$data3.event) === null || _payload$data3$event === void 0 ? void 0 : _payload$data3$event.data) !== null && _data !== void 0 ? _data : {});
        try {
          return `tracker.trackSelfDescribingEvent({\n  event: {\n    schema: '${eventSchema}',\n    data: ${eventData}\n  },\n  context: [\n${contextList.map(c => `    {\n      schema: '${c.schema}',\n      data: ${indentData(c.data)}\n    }`).join(',\n')}\n  ]\n})`;
        } catch (_unused2) {
          return ``;
        }
      };
      const MAX_JOURNEY_EVENTS = 10;

      /** Fixed height so Web/App columns stay aligned per journey row */
      const JOURNEY_CODE_BOX_HEIGHT_PX = 280;
      const renderCodeBlock = payload => /*#__PURE__*/jsxs("div", {
        style: {
          display: 'flex',
          flexDirection: 'column',
          minHeight: 0,
          flex: 1
        },
        children: [/*#__PURE__*/jsxs(Flex, {
          children: [payload.type === 'Web' ? /*#__PURE__*/jsx(DesktopOutlined, {}) : /*#__PURE__*/jsx(MobileOutlined, {}), /*#__PURE__*/jsxs(Typography.Text, {
            type: "secondary",
            children: [' ', /*#__PURE__*/jsxs("b", {
              children: [" ", payload.type, " Event"]
            })]
          })]
        }), /*#__PURE__*/jsxs("div", {
          style: {
            position: 'relative',
            marginTop: 8,
            height: JOURNEY_CODE_BOX_HEIGHT_PX,
            minHeight: 0,
            flexShrink: 0
          },
          children: [/*#__PURE__*/jsx("div", {
            style: {
              height: '100%',
              overflow: 'auto',
              background: 'rgba(150, 150, 150, 0.1)',
              borderRadius: 6
            },
            children: /*#__PURE__*/jsx("pre", {
              style: {
                margin: 0,
                padding: '12px 40px 12px 12px',
                fontFamily: 'monospace',
                fontSize: 12,
                whiteSpace: 'pre',
                overflow: 'visible'
              },
              children: payload.type === 'Web' ? eventString(payload) : appEventString(payload)
            })
          }), /*#__PURE__*/jsx(Button, {
            type: "text",
            size: "small",
            icon: /*#__PURE__*/jsx(CopyOutlined, {}),
            onClick: () => {
              navigator.clipboard.writeText(payload.type === 'Web' ? eventString(payload) : appEventString(payload));
              message.success('Copied!');
            },
            style: {
              position: 'absolute',
              top: 8,
              right: 8,
              zIndex: 1
            },
            "aria-label": "Copy code"
          })]
        })]
      });
      const AnalyticsJourneyTracker = () => {
        const [journeyEvents, setJourneyEvents] = useState(() => {
          if (!readJourneyTrackerEnabledFromSession()) return [];
          return readJourneyEventsFromSession();
        });
        const [journeyTrackerEnabled, setJourneyTrackerEnabled] = useState(readJourneyTrackerEnabledFromSession);

        // Keep analytics-dev-event aligned with journey tracker (handlers read both)
        useEffect(() => {
          const enabled = readJourneyTrackerEnabledFromSession();
          analyticsHelpers.storageManagement._setStorage('sessionStorage', DEV_EVENT_KEY, enabled);
          if (!enabled) {
            clearJourneyEventsFromSession();
          }
        }, []);
        useEffect(() => {
          if (!journeyTrackerEnabled) return;
          writeJourneyEventsToSession(journeyEvents);
        }, [journeyEvents, journeyTrackerEnabled]);
        const onJourneyTrackerChange = useCallback(checked => {
          setJourneyTrackerEnabled(checked);
          analyticsHelpers.storageManagement._setStorage('sessionStorage', DEV_EVENT_KEY, checked);
          analyticsHelpers.storageManagement._setStorage('sessionStorage', JOURNEY_TRACKER_KEY, checked);
          if (!checked) {
            setJourneyEvents([]);
            clearJourneyEventsFromSession();
          }
        }, []);
        const clearJourney = useCallback(() => {
          setJourneyEvents([]);
          clearJourneyEventsFromSession();
        }, []);
        useEffect(() => {
          const handler = ev => {
            var _webEventRaw$eventNam, _webEventRaw$data;
            analyticsHelpers.storageManagement._setStorage('sessionStorage', 'analytics-dev-event', true);
            const webEventRaw = analyticsHelpers.storageManagement._getStorage('sessionStorage', 'analytics-dev-web-event');
            const appFromStorage = analyticsHelpers.storageManagement._getStorage('sessionStorage', 'analytics-dev-app-event');
            const ce = ev;
            const appPayload = ce.detail && typeof ce.detail === 'object' && ce.detail !== null ? ce.detail : appFromStorage !== null && appFromStorage !== void 0 ? appFromStorage : {};
            const entry = {
              id: `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
              at: Date.now(),
              web: {
                eventName: (_webEventRaw$eventNam = webEventRaw === null || webEventRaw === void 0 ? void 0 : webEventRaw.eventName) !== null && _webEventRaw$eventNam !== void 0 ? _webEventRaw$eventNam : '',
                data: (_webEventRaw$data = webEventRaw === null || webEventRaw === void 0 ? void 0 : webEventRaw.data) !== null && _webEventRaw$data !== void 0 ? _webEventRaw$data : {}
              },
              app: appPayload
            };
            setJourneyEvents(prev => {
              const next = [entry, ...prev];
              return next.length > MAX_JOURNEY_EVENTS ? next.slice(0, MAX_JOURNEY_EVENTS) : next;
            });
            analyticsHelpers.storageManagement._deleteStorage('sessionStorage', 'analytics-dev-web-event');
            analyticsHelpers.storageManagement._deleteStorage('sessionStorage', 'analytics-dev-app-event');
          };
          document.addEventListener('analytics-dev-tracker-event', handler);
          return () => {
            document.removeEventListener('analytics-dev-tracker-event', handler);
          };
        }, []);
        return /*#__PURE__*/jsxs(Flex, {
          vertical: true,
          gap: "middle",
          children: [/*#__PURE__*/jsxs(Flex, {
            align: "center",
            gap: "middle",
            wrap: true,
            children: [/*#__PURE__*/jsx(Checkbox, {
              checked: journeyTrackerEnabled,
              onChange: e => onJourneyTrackerChange(e.target.checked),
              children: "Enable Journey Tracker"
            }), /*#__PURE__*/jsxs(Button, {
              size: "small",
              disabled: journeyEvents.length === 0,
              onClick: clearJourney,
              children: ["Clear journey (", journeyEvents.length, ")"]
            })]
          }), /*#__PURE__*/jsx("div", {
            style: {
              maxHeight: 'min(75vh, 900px)',
              overflowY: 'auto',
              paddingRight: 4
            },
            children: journeyEvents.length === 0 ? /*#__PURE__*/jsx(Typography.Text, {
              type: "secondary",
              children: "No events captured yet."
            }) : journeyEvents.map(entry => /*#__PURE__*/jsxs("div", {
              style: {
                marginBottom: 20,
                paddingBottom: 16,
                borderBottom: '1px solid rgba(0, 0, 0, 0.08)'
              },
              children: [/*#__PURE__*/jsxs(Typography.Text, {
                type: "secondary",
                style: {
                  fontSize: 12,
                  display: 'block',
                  marginBottom: 8
                },
                children: [new Date(entry.at).toLocaleString(), " \xB7 ", entry.web.eventName || '(no name)']
              }), /*#__PURE__*/jsxs(Flex, {
                gap: 16,
                align: "flex-start",
                wrap: "wrap",
                children: [/*#__PURE__*/jsxs("div", {
                  style: {
                    flex: '1 1 280px',
                    minWidth: 0,
                    display: 'flex',
                    flexDirection: 'column'
                  },
                  children: [/*#__PURE__*/jsx(Typography.Text, {
                    strong: true,
                    style: {
                      marginBottom: 4
                    },
                    children: "Web (sendAnalyticsEvent)"
                  }), renderCodeBlock({
                    type: 'Web',
                    eventName: entry.web.eventName,
                    data: entry.web.data
                  })]
                }), /*#__PURE__*/jsxs("div", {
                  style: {
                    flex: '1 1 280px',
                    minWidth: 0,
                    display: 'flex',
                    flexDirection: 'column'
                  },
                  children: [/*#__PURE__*/jsx(Typography.Text, {
                    strong: true,
                    style: {
                      marginBottom: 4
                    },
                    children: "App (Snowplow self-describing)"
                  }), renderCodeBlock({
                    type: 'App',
                    eventName: 'app',
                    data: entry.app
                  })]
                })]
              })]
            }, entry.id))
          })]
        });
      };

      const DevtoolsAnalytics = exports('D', () => {
        const tabItems = [{
          key: 'trigger',
          label: '🚀 Trigger Events',
          children: /*#__PURE__*/jsx(AnalyticsTriggerEvents, {})
        }, {
          key: 'journey',
          label: '📝 Track Journey',
          children: /*#__PURE__*/jsx(AnalyticsJourneyTracker, {})
        }];
        return /*#__PURE__*/jsx("div", {
          style: {
            width: '100%',
            padding: 0
          },
          children: /*#__PURE__*/jsx(Tabs, {
            type: "card",
            items: tabItems
          })
        });
      });

    })
  };
}));
//# sourceMappingURL=dev-tools-fee04f40.js.map
