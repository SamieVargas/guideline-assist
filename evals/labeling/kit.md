# QA hand-labeling kit (20 items)

For each item, read the guideline section and the transcript, then fill the matching rows of `labels.csv`: one status per required step from followed, missed, out_of_order, wrong_value, not_applicable, and the turn number it points to (blank for missed / not_applicable). Some items may contain a planted defect and some may not; the kit does not say which. Label before looking at any model QA output.

## L01 · subflow `status_quantity`

Required steps in order: pull-up-account -> verify-identity -> ask-the-oracle -> shipping-status -> offer-refund

<details><summary>Guideline section</summary>

```
### SECTION order_issue/status_quantity :: Order Issue / Status Quantity
Flow: Order Issue (get status of an order or change an order, possibly shipping)
Required action sequence: pull-up-account -> verify-identity -> ask-the-oracle -> shipping-status -> offer-refund
Actions this section lists: pull-up-account, verify-identity, ask-the-oracle, shipping-status, offer-refund
- The email confirmation of the order does not match the desired order quantity.
- Whether or not the conversation is successful depends on how happy you think the customer ended up. There is no right or wrong answer, just make your best judgement.
Step 1 [Pull up Account -> pull-up-account]: Get Full Name or Account ID for [Pull up Account]
Step 2 [Verify Identity -> verify-identity]: Start by looking up the order using the [Verify Identity] fields.
    * Full name - may have gotten this earlier
    * Account ID - may have gotten this earlier
    * Order ID
Step 3 [Ask the Oracle -> ask-the-oracle]: To decide whether or not this is a valid error:
    * Check if the email is accurate by 'Asking the Oracle' which will return Yes or No
    * If the email was wrong (Oracle returns No), then assure the customer that they were only charged for one item and that the email was wrong. Skip the following steps and [End Conversation] after explaining.
    * If the email was right (Oracle returns Yes), then it is a company mistake.  Continue to the next step below.
Step 4 [Shipping Status -> shipping-status]: (Only if Oracle says Yes) Find out whether the item has already shipped.
    * Ask for the shipping status from the customer and then submit using [Shipping Status]
    * If the item is Order Received, then immediately offer the refund and tell the customer the unwanted item has been removed from their order.
    * If the item is 'In Transit', 'Out for Delivery' or 'Delivered' then they must wait until the item arrives and call back to customer support to start the return process.
Step 5 [Offer Refund -> offer-refund]: (Only if Oracle says Yes) Find out how much the item cost
    * Ask the customer how much is the cost of the item meant to be returned
    * Enter that into the form and select the [Offer Refund] option
```
</details>

```
[0] AGENT: Hello, how can I help you today?
[1] CUSTOMER: Hi, I want to check my order status
[2] CUSTOMER: I only ordered one item but the email says I ordered two...
[3] AGENT: May I have your full name or your account ID?
[4] CUSTOMER: Yeah, my name is Alessandro Phoenix
[5] ACTION pull-up-account(alessandro phoenix) :: Account has been pulled up for Alessandro Phoenix.
[6] CUSTOMER: And the order ID is 4967029823
[7] AGENT: And may I have the account ID also?
[8] CUSTOMER: Yeah my account ID is IE2AFFH2AX
[9] ACTION verify-identity(alessandro phoenix, ie2affh2ax, 4967029823) :: Identity verification in progess ...
[10] ACTION ask-the-oracle() :: Querying the system for an answer ...
[11] AGENT: Ok, there does appear to have been an error on our end.
[12] AGENT: Has the item already shipped?
[13] CUSTOMER: Yeah, it says the order is out for delivery
[14] ACTION shipping-status(out for delivery) :: Shipping status of out for delivery has been noted.
[15] AGENT: Unfortunately you will have to wait until the items are received to begin the return process.
[16] AGENT: I can offer a refund right now for you.
[17] CUSTOMER: Okay, a refund right now sounds great
[18] AGENT: How much was the cost of the item?
[19] CUSTOMER: $74
[20] ACTION offer-refund(74) :: A refund has been made for the amount of $74.
[21] CUSTOMER: Awesome, thanks!
[22] AGENT: Ok, the refund has been submitted and please contact us when you receive the item to begin the return process.
[23] AGENT: Is there anything else I can help you with today?
[24] CUSTOMER: Nope, thats it. Thank you!
[25] AGENT: Have a great day.
```

## L02 · subflow `bad_price_competitor`

Required steps in order: pull-up-account -> record-reason -> verify-identity -> promo-code

<details><summary>Guideline section</summary>

```
### SECTION purchase_dispute/bad_price_competitor :: Purchase Dispute / Bad Price Competitor
Flow: Purchase Dispute (bad price, out of stock, promo codes, billing)
Required action sequence: pull-up-account -> record-reason -> verify-identity -> promo-code
Actions this section lists: pull-up-account, record-reason, verify-identity, promo-code
- The customer is calling in to call about a bad price.   The customer will give the reason the competitor has a better price.
- Wrap up as usual.
Step 1 [Pull up Account -> pull-up-account]: All chats in this flow start by asking the customer for their full name or Account ID with [Pull up account].
    * This loads information in the background related to this user.
Step 2 [Record Reason -> record-reason]: Find out why they are disputing a purchase price
    * Either 'competitor' or 'yesterday'
    * Enter this into the input box and [Record Reason]
Step 3 [Verify Identity -> verify-identity]: Check if this is a valid order by gathering the following info, then [Verify Identity]
    * Full name - may have gotten this earlier
    * Account ID - may have gotten this earlier
    * Order ID
Step 4 [N/A -> no action (talk to the customer)]: Try to convince the customer that sometimes the prices change, and that is outside of your control.
    * For example, Our pricing algorithms will often dynamically change the price of an item.
Step 5 [Promo Code -> promo-code]: If they are still unhappy:
    * If the customer keeps pushing, offer them a discount using [Promo Code]
    * You do not need to enter any information.
    * Generate the code and share that with them
```
</details>

```
[0] CUSTOMER: Hi
[1] CUSTOMER: I have an issue with an item
[2] AGENT: Hi thanks for contacting AcmeBrands.
[3] AGENT: What seems to be the issue?
[4] CUSTOMER: I need a new jacket because I am going on a trip to see the Northern Lights in Canada soon
[5] CUSTOMER: I like this jacket on your site
[6] CUSTOMER: But it's soooo overpriced
[7] CUSTOMER: I can get it on other prices for much less
[8] CUSTOMER: I am very frustrated by this because I like your site and I am loyal to you
[9] CUSTOMER: But I don't want to spend more money
[10] CUSTOMER: You are selling this Guess jacket for $95
[11] CUSTOMER: I mean $94
[12] AGENT: Ok sure. I understand where you are coming from.
[13] CUSTOMER: I have seen it on other sites for like $40 or so
[14] AGENT: To begin, can I get your full name or Account ID please?
[15] CUSTOMER: David Williams
[16] CUSTOMER: KOCHTRCZKI
[17] ACTION pull-up-account(david williams) :: Account has been pulled up for David Williams.
[18] AGENT: Thank you Mr. Williams.
[19] AGENT: So, our competitors are offering that item at a lower price than us, correct?
[20] CUSTOMER: Yes they are
[21] CUSTOMER: Why is your item so much more money?
[22] ACTION record-reason(competitor) :: A reason of competitor has been recorded.
[23] AGENT: I can look into that for you. But first I'm going to need your Order ID please.
[24] CUSTOMER: Okay, it's 1867616599
[25] ACTION verify-identity(david williams, kochtzczkr, 1867616599) :: Identity verification in progess ...
[26] AGENT: Thanks.
[27] AGENT: I understand your frustration, the reason sometimes our prices are more expensive is that our pricing is determined on the fly by an AI algorithm.
[28] CUSTOMER: Okay but they made a mistake this time
[29] AGENT: So they can change dynamically.
[30] CUSTOMER: Can you offer the jacket to me for less
[31] CUSTOMER: I am a loyal Silver member
[32] AGENT: I do apologize for the inconvenience. What I can do is offer you a promo code if you would like?
[33] CUSTOMER: Yes that would be great
[34] CUSTOMER: I have seen the jacket for $40 elsewhere
[35] CUSTOMER: So I would like at least 50% off
[36] AGENT: Ok, what I can do is generate a promo code for you for $54 off
[37] CUSTOMER: Yes!!! That would be great
[38] AGENT: so that should bring the price down to $40
[39] CUSTOMER: Then I can wear the jacket in Canada
[40] ACTION promo-code() :: A promo code has been created.
[41] AGENT: Absolutely.
[42] ACTION promo-code() :: A promo code has been created.
[43] CUSTOMER: Thank so much
[44] CUSTOMER: This means a lot to me
[45] AGENT: Your promo code is 6WVVA.
[46] CUSTOMER: Great! I am very happy with this
[47] AGENT: You're welcome. We value your business.
[48] CUSTOMER: That's all I needed
[49] AGENT: Is there anything else I can help you with?
[50] CUSTOMER: Thanks for your help
[51] AGENT: Alright then, have a fantastic day!
[52] CUSTOMER: I don't need anything else
[53] CUSTOMER: You also
```

## L03 · subflow `policy`

Required steps in order: search-faq -> search-policy -> select-faq

<details><summary>Guideline section</summary>

```
### SECTION storewide_query/policy :: Storewide Query / Policy FAQ
Flow: Storewide Query (FAQ questions about pricing, timing, membership or features)
Required action sequence: search-faq -> search-policy -> select-faq
Actions this section lists: search-faq, search-policy, select-faq
- The main effort is in figuring out which question the customer is asking:
- Canceling subscriptions, Late on a subscription payment, Refund policy, Return policy
Step 1 [Search FAQ -> search-faq]: When you realize that the customer is asking something that can be found in the FAQ, click the [Search FAQ] button
    * This will swap out for a different view that has FAQ content
    * If you made an error, just click [Hide FAQ] to switch back
Step 2 [Policy -> search-policy]: Decide which kind of question the customer is asking about:
    * Possible options are Pricing, Timing, Membership and Policies
    * Click the policy toggle switch
    * This will record an action, so try to get this decision correct.
    * The flow diagram allows you to see all the questions at once.
Step 3 [Select Answer -> select-faq]: Read through the list of 4 options
    * Click [Select Answer] for the correct answer to the customer’s question
    * Remember the category for the survey later
Step 4 [N/A -> no action (talk to the customer)]: The automated system response does not include all the information, so make sure to explain the details in natural language.
    * You should not copy/paste
```
</details>

```
[0] AGENT: Thank you for contacting Acme Brands. How can I help you?
[1] CUSTOMER: Hello, I would like to know what the return policy is as I am looking to purchase something
[2] AGENT: Okay, I can help you with that, but first can I have your name?
[3] CUSTOMER: Albert Sanders
[4] ACTION search-policy() :: System Action: search policy
[5] ACTION select-faq(policy_1) :: FAQ answer related to policy (question1) was selected.
[6] AGENT: Our return policies are based on your membership level. Gold member have unlimited returns, silver can return for 6 months and bronze can make returns within 90 days.
[7] AGENT: All other members have just 30 days to make a return.
[8] CUSTOMER: Ok great, thank you
[9] AGENT: You're welcome. Is there anything else I can help with?
[10] CUSTOMER: that is all
[11] AGENT: Great! I hope you enjoy the rest of your day.
```

## L04 · subflow `jeans`

Required steps in order: search-faq -> search-jeans -> select-faq

<details><summary>Guideline section</summary>

```
### SECTION single_item_query/jeans :: Single-Item Query / Jeans FAQ
Flow: Single-Item Query (FAQ questions about jeans, boots, shirt or sweater)
Required action sequence: search-faq -> search-jeans -> select-faq
Actions this section lists: search-faq, search-jeans, select-faq
- The main effort is in figuring out which question the customer is asking:
- how to remove a grass stain, how often does this need to be washed, how long is the leg length, cost to get it tailored, shrink after washing, dark blue or black color, any in a larger/smaller size, design with ripped holes in them
Step 1 [Search FAQ -> search-faq]: When you realize that the customer is asking something that can be found in the FAQ, click the [Search FAQ] button
    * This will swap out for a different view that has FAQ content
    * If you made an error, just click [Hide FAQ] to switch back
Step 2 [Jeans -> search-jeans]: Decide which article of clothing the customer is asking about:
    * Possible options are Jeans, Shirt, Boots and Jacket
    * Click the jeans toggle switch
    * This will record an action, so try to get this decision correct
    * The flow diagram allows you to see all the questions at once.
Step 3 [Select Answer -> select-faq]: Read through the list of 8 options
    * Select the correct answer for the customer’s question with [Select Answer]
    * Remember the question your selected for the survey later
Step 4 [N/A -> no action (talk to the customer)]: The system created response does not include all the information, so make sure to explain the details in natural language.
    * Do not copy/paste.
```
</details>

```
[0] CUSTOMER: ICould you please clarify the color I’m not sure if they are dark blue or black
[1] AGENT: Welcome to AcmeBrands. How may I help you?
[2] CUSTOMER: Albert Sanders
[3] AGENT: OK. The color of what item?
[4] CUSTOMER: Michael kors jeans
[5] AGENT: Sure. Let me look into that.
[6] ACTION search-faq() :: Searching the FAQ pages ...
[7] ACTION search-jeans() :: System Action: search jeans
[8] AGENT: Yes. We have many available colors: deep sea, indigo, equinox, indie blue, sky blue.
[9] AGENT: There are also various shades of brown and black as well.
[10] AGENT: I hope this helps.
[11] ACTION select-faq(jeans_other_2) :: FAQ answer related to jeans (other2) was selected.
[12] CUSTOMER: Ok
[13] AGENT: Is there anything else I can help with?
[14] CUSTOMER: So I’d say dark blue
[15] AGENT: Yes. We have that color.
[16] CUSTOMER: Have a good day
[17] AGENT: You too.
```

## L05 · subflow `recover_password`

Required steps in order: pull-up-account -> enter-details -> make-password

<details><summary>Guideline section</summary>

```
### SECTION account_access/recover_password :: Account Access / Recover Password
Flow: Account Access (username, password, and two-factor authentication)
Required action sequence: pull-up-account -> enter-details -> make-password
Actions this section lists: pull-up-account, enter-details, make-password
- Help the customer get a new password
- Share the password with the customer.
Step 1 [Pull up Account -> pull-up-account]: Get Full Name or Account ID for [Pull up Account]
Step 2 [Enter Details -> enter-details]: Get the customer’s username to check their identity
    * If they don’t have their username, then follow the 'Recover Username' flow above
    * Once you have it, enter the username and click on [Enter Details]
Step 3 [N/A -> no action (talk to the customer)]: Tell the customer you cannot get their password, but you can generate a new one for them.
Step 4 [Make Password -> make-password]: To operate the [Make Password] action, you will first need:
    * Pin Number <or> answer to the Security Question
    * Enter either value into the box and then click the [Make Password] button
```
</details>

```
[0] AGENT: Hello, how may I help you?
[1] CUSTOMER: I need to sign into my account and have forgotten my password :(
[2] AGENT: I can help you recover that, could I get your full name, please?
[3] CUSTOMER: Rodriguez Domingo
[4] AGENT: Thanks, Rodriguez
[5] ACTION pull-up-account(rodriguez domingo) :: Account has been pulled up for Rodriguez Domingo.
[6] AGENT: Do you happen to know your username?
[7] CUSTOMER: rodriguezd727
[8] ACTION enter-details(rodriguezd727) :: Details of rodriguezd727 have been entered.
[9] AGENT: Thank you, now for your password I can generate a new one for you. I'll need the email associated with the account.
[10] CUSTOMER: rodriguezd727@email.com
[11] AGENT: Finally, I'll just need your PIN number or mother's maiden name for security purposes.
[12] CUSTOMER: pin # 7432
[13] AGENT: Your new password is 6yh9j4f39g9 . Is there anything else I can do for you?
[14] CUSTOMER: Nope that's all  Thank you!
[15] AGENT: Have a good day!
```

## L06 · subflow `recover_password`

Required steps in order: pull-up-account -> enter-details -> make-password

<details><summary>Guideline section</summary>

```
### SECTION account_access/recover_password :: Account Access / Recover Password
Flow: Account Access (username, password, and two-factor authentication)
Required action sequence: pull-up-account -> enter-details -> make-password
Actions this section lists: pull-up-account, enter-details, make-password
- Help the customer get a new password
- Share the password with the customer.
Step 1 [Pull up Account -> pull-up-account]: Get Full Name or Account ID for [Pull up Account]
Step 2 [Enter Details -> enter-details]: Get the customer’s username to check their identity
    * If they don’t have their username, then follow the 'Recover Username' flow above
    * Once you have it, enter the username and click on [Enter Details]
Step 3 [N/A -> no action (talk to the customer)]: Tell the customer you cannot get their password, but you can generate a new one for them.
Step 4 [Make Password -> make-password]: To operate the [Make Password] action, you will first need:
    * Pin Number <or> answer to the Security Question
    * Enter either value into the box and then click the [Make Password] button
```
</details>

```
[0] AGENT: Hey there, how may I be of service?
[1] CUSTOMER: hola, I'm trying to check my order status but I forgot my password
[2] AGENT: i see, so you need help recovering your password? I can help you with that today
[3] CUSTOMER: thanks
[4] AGENT: First i need your full name to pull up the account
[5] CUSTOMER: Albert Sanders
[6] ACTION pull-up-account(albert sanders) :: Account has been pulled up for Albert Sanders.
[7] AGENT: and may ihave your username please?
[8] CUSTOMER: asanders293
[9] ACTION make-password() :: A password has been generated.
[10] AGENT: I cannot give you the current password, however I can reset it for you
[11] CUSTOMER: that works
[12] AGENT: to do so, i will need either your pin number, or to answer your secret question
[13] AGENT: do you have the pin handy?
[14] CUSTOMER: nope
[15] AGENT: alright, then we will need the answer to the secret question
[16] AGENT: what is your mothers maiden name
[17] CUSTOMER: Ahmed
[18] ACTION enter-details(asanders293) :: Details of asanders293 have been entered.
[19] AGENT: 8vlw0wl7lyl is your new password
[20] AGENT: Did you have anything else you wanted assistance with today?
[21] CUSTOMER: no, thanks a lot
[22] AGENT: Goodbye!
```

## L07 · subflow `manage_create`

Required steps in order: pull-up-account -> verify-identity -> shipping-status -> membership -> make-purchase

<details><summary>Guideline section</summary>

```
### SECTION order_issue/manage_create :: Order Issue / Manage Create
Flow: Order Issue (get status of an order or change an order, possibly shipping)
Required action sequence: pull-up-account -> verify-identity -> shipping-status -> membership -> make-purchase
Actions this section lists: pull-up-account, verify-identity, shipping-status, membership, make-purchase
- The customer wants to add something to their existing order.
- If the new item cannot be added to the order, then apologize to the customer and remember to mark the conversation as complete, but not successful in the survey.
Step 1 [Pull up Account -> pull-up-account]: Get Full Name or Account ID for [Pull up Account]
Step 2 [Verify Identity -> verify-identity]: Start by looking up the order using the [Verify Identity] fields.
    * Full name - may have gotten this earlier
    * Account ID - may have gotten this earlier
    * Order ID
Step 3 [Shipping Status -> shipping-status]: Find out whether the item has already shipped.
    * Ask the customer for the shipping status, and enter into [Shipping Status]
    * If the item is Order Received, then skip the next step and directly update the order.
    * If the item is 'In Transit', 'Out for Delivery', or 'Delivered' then it is too late.  Move to the next step (membership level).
Step 4 [Membership Privileges -> membership]: Silver and Gold members get special treatment.  Ask the customer for their membership level, if they qualify:
    * Enter the Gold or Silver level.  Their existing order is already out for delivery, so instead you will ship the new item to them ASAP in a separate order with no shipping fee.
    * Choose the [Membership Privileges] option
Step 5 [Make Purchase -> make-purchase]: To add to an item to the order you will need to enter its name
    * Enter a phrase of brand and item, such as 'Guess Jeans' or 'Calvin Klein Shirt'
    * Then select [Make Purchase]
```
</details>

```
[0] AGENT: Hello, how may I help you today?
[1] CUSTOMER: hello I'd like to add an item to an already ordered order if it's possible
[2] CUSTOMER: your site tells me it's in transit
[3] AGENT: I'd be happy to help, can you give me either your full name or account ID?
[4] CUSTOMER: Joyce Wu
[5] CUSTOMER: D5WE1SEBSC
[6] ACTION pull-up-account(joyce wu) :: Account has been pulled up for Joyce Wu.
[7] AGENT: Thank you, next can you send me your order ID so I can pull up the order?
[8] CUSTOMER: order number is 3253443846
[9] CUSTOMER: if it's possible I'd like to add on the calvin klein shirt
[10] ACTION verify-identity(joyce wu, d5we1sebsc, 3253443846) :: Identity verification in progress ...
[11] AGENT: Let's see what we can do, it's a little tricky since the order is already in transit. Can you give me your membership level? The process is a little different for each level. In the meantime, I'm going to note the delivery status.
[12] CUSTOMER: it's silver hope that helps
[13] ACTION shipping-status(order received) :: Shipping status of Order Received has been noted.
[14] AGENT: Yes, it does! Since you are a silver member, I can go ahead and get a new shipment out at no delivery cost to you. Let me put that in the system.
[15] ACTION membership(silver) :: Membership level of Silver has been noted.
[16] CUSTOMER: ok I suppose that fixes my problem to
[17] CUSTOMER: thanks!
[18] AGENT: Ok, I'll go ahead and put in a delivery request for the shirt.
[19] ACTION make-purchase(calvin klein shirt) :: A purchase of Calvin Klein shirt was made.
[20] AGENT: Ok, you should be getting a confirmation about that item shortly with delivery information. Is there anything else I can help with?
[21] CUSTOMER: that's all thanks so much
[22] AGENT: Great, enjoy the rest of your day!
```

## L08 · subflow `jacket`

Required steps in order: search-faq -> search-jacket -> select-faq

<details><summary>Guideline section</summary>

```
### SECTION single_item_query/jacket :: Single-Item Query / Jacket FAQ
Flow: Single-Item Query (FAQ questions about jeans, boots, shirt or sweater)
Required action sequence: search-faq -> search-jacket -> select-faq
Actions this section lists: search-faq, search-jacket, select-faq
- The main effort is in figuring out which question the customer is asking:
- how to remove a wine stain, washer or dry-clean only, how long is the arm length, how do you detach the hood, shrink after washing, if the store has any in stock, what material is this made of, is this warm enough to wear
Step 1 [Search FAQ -> search-faq]: When you realize that the customer is asking something that can be found in the FAQ, click the [Search FAQ] button
    * This will swap out for a different view that has FAQ content
    * If you made an error, just click [Hide FAQ] to switch back
Step 2 [Jacket -> search-jacket]: Decide which article of clothing the customer is asking about:
    * Possible options are Jeans, Shirt, Boots and Jacket
    * Click the jacket toggle switch
    * This will record an action, so try to get this decision correct
    * The flow diagram allows you to see all the questions at once.
Step 3 [Select Answer -> select-faq]: Read through the list of 8 options
    * Select the correct answer for the customer’s question with [Select Answer]
    * Remember the question your selected for the survey later
Step 4 [N/A -> no action (talk to the customer)]: The system created response does not include all the information, so make sure to explain the details in natural language.
    * Do not copy/paste.
```
</details>

```
[0] AGENT: How can I help you today?
[1] CUSTOMER: I am looking at the Calvin Klein jacket and would like to know if it shrinks after washing
[2] AGENT: Okay, let me look
[3] ACTION search-faq() :: Searching the FAQ pages ...
[4] ACTION search-jacket() :: System Action: search jacket
[5] ACTION select-faq(jacket_other_1) :: FAQ answer related to jacket (other1) was selected.
[6] AGENT: Nope, though you should be wary of over drying it. We recommend line drying or using low heat
[7] AGENT: Is there anything else I can do for you?
[8] CUSTOMER: ok. Thank you
[9] CUSTOMER: no that is all
[10] AGENT: Then have a nice day!
```

## L09 · subflow `recover_password`

Required steps in order: pull-up-account -> enter-details -> make-password

<details><summary>Guideline section</summary>

```
### SECTION account_access/recover_password :: Account Access / Recover Password
Flow: Account Access (username, password, and two-factor authentication)
Required action sequence: pull-up-account -> enter-details -> make-password
Actions this section lists: pull-up-account, enter-details, make-password
- Help the customer get a new password
- Share the password with the customer.
Step 1 [Pull up Account -> pull-up-account]: Get Full Name or Account ID for [Pull up Account]
Step 2 [Enter Details -> enter-details]: Get the customer’s username to check their identity
    * If they don’t have their username, then follow the 'Recover Username' flow above
    * Once you have it, enter the username and click on [Enter Details]
Step 3 [N/A -> no action (talk to the customer)]: Tell the customer you cannot get their password, but you can generate a new one for them.
Step 4 [Make Password -> make-password]: To operate the [Make Password] action, you will first need:
    * Pin Number <or> answer to the Security Question
    * Enter either value into the box and then click the [Make Password] button
```
</details>

```
[0] AGENT: Hi, AcmeBrands here. How can I help you?
[1] CUSTOMER: Hello
[2] CUSTOMER: I want to see my shopping history
[3] CUSTOMER: But I forgot my password
[4] AGENT: Okay, can I have your username?
[5] CUSTOMER: Yes my username is crystalm686
[6] AGENT: I will also need your full name or account ID.
[7] CUSTOMER: My name is Crystal Minh
[8] AGENT: Thank you.
[9] ACTION enter-details(crystalm686) :: Details of crystalm686 have been entered.
[10] ACTION pull-up-account(crystal minh) :: Account has been pulled up for Crystal Minh.
[11] AGENT: I can't get your old password, but I can generate a new one for you.
[12] AGENT: I will need either your PIN number or your security question answer.
[13] CUSTOMER: Ok my security answer is Martinez
[14] ACTION make-password() :: A password has been generated.
[15] AGENT: Thank you, here is your new password: ggbszawojpk
[16] CUSTOMER: Thanks! Now I have to go change it. I appreciate it.
[17] AGENT: You're welcome, is there anything else you need?
[18] CUSTOMER: No, that's all thank you
[19] AGENT: Okay, have a nice day.
```

## L10 · subflow `policy`

Required steps in order: search-faq -> search-policy -> select-faq

<details><summary>Guideline section</summary>

```
### SECTION storewide_query/policy :: Storewide Query / Policy FAQ
Flow: Storewide Query (FAQ questions about pricing, timing, membership or features)
Required action sequence: search-faq -> search-policy -> select-faq
Actions this section lists: search-faq, search-policy, select-faq
- The main effort is in figuring out which question the customer is asking:
- Canceling subscriptions, Late on a subscription payment, Refund policy, Return policy
Step 1 [Search FAQ -> search-faq]: When you realize that the customer is asking something that can be found in the FAQ, click the [Search FAQ] button
    * This will swap out for a different view that has FAQ content
    * If you made an error, just click [Hide FAQ] to switch back
Step 2 [Policy -> search-policy]: Decide which kind of question the customer is asking about:
    * Possible options are Pricing, Timing, Membership and Policies
    * Click the policy toggle switch
    * This will record an action, so try to get this decision correct.
    * The flow diagram allows you to see all the questions at once.
Step 3 [Select Answer -> select-faq]: Read through the list of 4 options
    * Click [Select Answer] for the correct answer to the customer’s question
    * Remember the category for the survey later
Step 4 [N/A -> no action (talk to the customer)]: The automated system response does not include all the information, so make sure to explain the details in natural language.
    * You should not copy/paste
```
</details>

```
[0] CUSTOMER: Hi
[1] AGENT: Hello, how can I help you today?
[2] CUSTOMER: I want to knowal about your refund policy
[3] AGENT: Okay, let me look into that for you.
[4] ACTION search-faq() :: Searching the FAQ pages ...
[5] CUSTOMER: I want to know about your refund policy because I want to buy some stuffs
[6] ACTION search-policy() :: System Action: search policy
[7] ACTION select-faq(policy_2) :: FAQ answer related to policy (question2) was selected.
[8] AGENT: Refunds are only available for items that haven't shipped yet
[9] AGENT: You'll need a valid order ID username and email in order for us to process one for you.
[10] AGENT: Is there anything else I can help you with?
[11] CUSTOMER: Okay.
[12] CUSTOMER: Thanks
[13] CUSTOMER: That will be all
[14] AGENT: Then have a nice day!
```

## L11 · subflow `jeans`

Required steps in order: search-faq -> search-jeans -> select-faq

<details><summary>Guideline section</summary>

```
### SECTION single_item_query/jeans :: Single-Item Query / Jeans FAQ
Flow: Single-Item Query (FAQ questions about jeans, boots, shirt or sweater)
Required action sequence: search-faq -> search-jeans -> select-faq
Actions this section lists: search-faq, search-jeans, select-faq
- The main effort is in figuring out which question the customer is asking:
- how to remove a grass stain, how often does this need to be washed, how long is the leg length, cost to get it tailored, shrink after washing, dark blue or black color, any in a larger/smaller size, design with ripped holes in them
Step 1 [Search FAQ -> search-faq]: When you realize that the customer is asking something that can be found in the FAQ, click the [Search FAQ] button
    * This will swap out for a different view that has FAQ content
    * If you made an error, just click [Hide FAQ] to switch back
Step 2 [Jeans -> search-jeans]: Decide which article of clothing the customer is asking about:
    * Possible options are Jeans, Shirt, Boots and Jacket
    * Click the jeans toggle switch
    * This will record an action, so try to get this decision correct
    * The flow diagram allows you to see all the questions at once.
Step 3 [Select Answer -> select-faq]: Read through the list of 8 options
    * Select the correct answer for the customer’s question with [Select Answer]
    * Remember the question your selected for the survey later
Step 4 [N/A -> no action (talk to the customer)]: The system created response does not include all the information, so make sure to explain the details in natural language.
    * Do not copy/paste.
```
</details>

```
[0] AGENT: Hi, there.  How may I help you?
[1] CUSTOMER: Could you tell me if the Michael Kors jeans will shrink after I wash them?
[2] AGENT: I sure can.  Let me pull up the item.
[3] CUSTOMER: Thank you
[4] ACTION search-faq() :: Searching the FAQ pages ...
[5] ACTION search-jeans() :: System Action: search jeans
[6] ACTION select-faq(jeans_other_1) :: FAQ answer related to jeans (other1) was selected.
[7] AGENT: If you wash the jeans according to the label recommendations, they should not shrink.
[8] CUSTOMER: Ok.  Thank you
[9] AGENT: Always fold them inside out and use the cold wash.
[10] AGENT: You can hang-dry them, which is recommended, or you can put them in the dryer and use Normal cycle.
[11] AGENT: Is there anything else I can help you with?
[12] CUSTOMER: No that is all
[13] AGENT: Have a great day!
```

## L12 · subflow `timing`

Required steps in order: search-faq -> search-timing -> select-faq

<details><summary>Guideline section</summary>

```
### SECTION storewide_query/timing :: Storewide Query / Timing FAQ
Flow: Storewide Query (FAQ questions about pricing, timing, membership or features)
Required action sequence: search-faq -> search-timing -> select-faq
Actions this section lists: search-faq, search-timing, select-faq
- The main effort is in figuring out which question the customer is asking:
- When does spring collection drop?, When does the local store open?, When does the annual sale begin?, When do the promo codes expire?
Step 1 [Search FAQ -> search-faq]: When you realize that the customer is asking something that can be found in the FAQ, click the [Search FAQ] button
    * This will swap out for a different view that has FAQ content
    * If you made an error, just click [Hide FAQ] to switch back
Step 2 [Timing -> search-timing]: Decide which kind of question the customer is asking about:
    * Possible options are Pricing, Timing, Membership and Policies
    * Click the timing toggle switch
    * This will record an action, so try to get this decision correct.
    * The flow diagram allows you to see all the questions at once.
Step 3 [Select Answer -> select-faq]: Read through the list of 4 options
    * Click [Select Answer] for the correct answer to the customer’s question
    * Remember the category for the survey later
Step 4 [N/A -> no action (talk to the customer)]: The automated system response does not include all the information, so make sure to explain the details in natural language.
    * You should not copy/paste
```
</details>

```
[0] AGENT: Hello. May I help you with anything today?
[1] CUSTOMER: Hi when can the promo code be used?
[2] AGENT: Do you currently have a promo code?
[3] CUSTOMER: I'm a gold member and have a code to use, I'm just shopping for now and thinking of purchasing if the code is valid
[4] AGENT: Sure. Are you having trouble with the promo code?
[5] CUSTOMER: I'm just confused as to when I can use it.
[6] AGENT: You can use when you make a purchase.
[7] CUSTOMER: Okay great .  Thank you.  I will make my purchase then.
[8] ACTION search-faq() :: Searching the FAQ pages ...
[9] ACTION search-policy() :: System Action: search policy
[10] ACTION search-membership() :: System Action: search membership
[11] ACTION search-policy() :: System Action: search policy
[12] ACTION search-timing() :: System Action: search timing
[13] AGENT: They are active for 7 days.
[14] CUSTOMER: O.k. that's what I needed to know.  Thanks for the info.
[15] AGENT: You should see the expiration date on it.
[16] CUSTOMER: Great, thanks for the help
[17] AGENT: So just to wrap up. You needed to know the time frame of using a promo code?
[18] ACTION select-faq(timing_4) :: FAQ answer related to timing (question4) was selected.
[19] CUSTOMER: Yes, and you said they are active for 7 days.
[20] AGENT: That is correct. Thank you very much.
```

## L13 · subflow `recover_password`

Required steps in order: pull-up-account -> enter-details -> make-password

<details><summary>Guideline section</summary>

```
### SECTION account_access/recover_password :: Account Access / Recover Password
Flow: Account Access (username, password, and two-factor authentication)
Required action sequence: pull-up-account -> enter-details -> make-password
Actions this section lists: pull-up-account, enter-details, make-password
- Help the customer get a new password
- Share the password with the customer.
Step 1 [Pull up Account -> pull-up-account]: Get Full Name or Account ID for [Pull up Account]
Step 2 [Enter Details -> enter-details]: Get the customer’s username to check their identity
    * If they don’t have their username, then follow the 'Recover Username' flow above
    * Once you have it, enter the username and click on [Enter Details]
Step 3 [N/A -> no action (talk to the customer)]: Tell the customer you cannot get their password, but you can generate a new one for them.
Step 4 [Make Password -> make-password]: To operate the [Make Password] action, you will first need:
    * Pin Number <or> answer to the Security Question
    * Enter either value into the box and then click the [Make Password] button
```
</details>

```
[0] AGENT: Hello. How can i help you today?
[1] CUSTOMER: Hi! I was trying to access my account online to check the status of my order but I seem to have forgotten my password
[2] CUSTOMER: I was hoping you could help me
[3] AGENT: Oh no. I'm sorry to hear that. I would be more than happy to help
[4] AGENT: Can I get your full name please?
[5] CUSTOMER: Rodriguez Domingo
[6] ACTION pull-up-account(rodriguez domingo) :: Account has been pulled up for Rodriguez Domingo.
[7] AGENT: Great, can I get your username as well?
[8] CUSTOMER: I am sorry I do not have that either. May be you could help me with that too?
[9] AGENT: Sure thing can you provide your zip code and phone number please?
[10] CUSTOMER: 37159
[11] CUSTOMER: (470) 948-1677
[12] ACTION verify-identity(rodriguez domingo, 37159, (470) 948-1677) :: Identity verification in progress ...
[13] AGENT: Your username is RDomingo1
[14] CUSTOMER: Thank you
[15] ACTION enter-details(rdomingo1) :: Details of RDomingo1 have been entered.
[16] AGENT: Alright can I get your pin number or the answer to your security question please?
[17] CUSTOMER: 155739
[18] ACTION make-password() :: A password has been generated.
[19] AGENT: Great
[20] AGENT: Although I cannot retreive your old password I have generated you a new one.
[21] CUSTOMER: Thank you
[22] AGENT: Your new password is as follows
[23] AGENT: scwien10f9
[24] CUSTOMER: Thank you so much
[25] AGENT: No problem is there anything else I can help you with today?
[26] CUSTOMER: That is all. Thank you
[27] AGENT: Have a great day!
```

## L14 · subflow `reset_2fa`

Required steps in order: pull-up-account -> enter-details -> send-link

<details><summary>Guideline section</summary>

```
### SECTION account_access/reset_2fa :: Account Access / Reset Two-Factor Auth
Flow: Account Access (username, password, and two-factor authentication)
Required action sequence: pull-up-account -> enter-details -> send-link
Actions this section lists: pull-up-account, enter-details, send-link
- Let the customer know that to reset, you will be sending a special code to their email.  To proceed:
- If the customer does not seem satisfied, then mark the conversation as not successful when filling out the survey.
Step 1 [Pull up Account -> pull-up-account]: Get Full Name or Account ID for [Pull up Account]
Step 2 [Enter Details -> enter-details]: You will need their email address so you can email them the reset code:
    * Enter their email address with the [Enter Details] action
    * If they don’t have their email address, you can bypass this problem by getting one of the following two items: > Ask for their PIN number > Tell them you are going to ask the security question, which is 'What is your mother’s maiden name?'
    * Then submit that value into the [Enter Details] form instead.  Tell them that you will send the reset code to the email address saved on file.  Feel free to make up an email address if the customer asks for it.
Step 3 [Send Link -> send-link]: Inform the customer that to be safe, they should also follow best practices for security.
    * Tell them you will send a link about security best practices
    * Then click the [Send Link] button, you do not need to enter anything into the form
```
</details>

```
[0] AGENT: Hello. How can i help you today?
[1] CUSTOMER: Oh man, well I placed an order but now I can't check on it because I lost my phone that as two factor authentication on it.
[2] AGENT: oh no!
[3] AGENT: Let's look into this together!
[4] CUSTOMER: Great
[5] AGENT: We can have a reset code sent to your email
[6] AGENT: Can I confirm your full name?
[7] CUSTOMER: Crystal Minh
[8] ACTION pull-up-account(crystal minh) :: Account has been pulled up for Crystal Minh.
[9] AGENT: can i get your email address as well?
[10] CUSTOMER: cminh01@email.com
[11] AGENT: I have sent a reset code to your email
[12] AGENT: Also in order to help you keep your account safe I've sent a link with additional resources
[13] ACTION send-link() :: A link will be sent.
[14] AGENT: Is there anything else I can do for you today?
[15] CUSTOMER: And I can get into it without the two factor authorization?
[16] AGENT: i have sent a code to reset your two factor authorization
[17] CUSTOMER: okay great, thanks
[18] AGENT: Is there anything else I can do for you today?
[19] CUSTOMER: that was it
[20] AGENT: All right. Well Thanks for reaching out and have a great day!
```

## L15 · subflow `boots`

Required steps in order: search-faq -> search-boots -> select-faq

<details><summary>Guideline section</summary>

```
### SECTION single_item_query/boots :: Single-Item Query / Boots FAQ
Flow: Single-Item Query (FAQ questions about jeans, boots, shirt or sweater)
Required action sequence: search-faq -> search-boots -> select-faq
Actions this section lists: search-faq, search-boots, select-faq
- The main effort is in figuring out which question the customer is asking
- how remove a paint stain, how wide is the shoe, how to remove gum, how long to wear in, waterproof, what is the lace color, desired size not in stock, comes with warranty
Step 1 [Search FAQ -> search-faq]: When you realize that the customer is asking something that can be found in the FAQ, click the [Search FAQ] button
    * This will swap out for a different view that has FAQ content
    * If you made an error, just click [Hide FAQ] to switch back
Step 2 [Boots -> search-boots]: Decide which article of clothing the customer is asking about:
    * Possible options are Jeans, Shirt, Boots and Jacket
    * Click the boots toggle switch
    * This will record an action, so try to get this decision correct
    * The flow diagram allows you to see all the questions at once.
Step 3 [Select Answer -> select-faq]: Read through the list of 8 options
    * Select the correct answer for the customer’s question with [Select Answer]
    * Remember the question your selected for the survey later
Step 4 [N/A -> no action (talk to the customer)]: The system created response does not include all the information, so make sure to explain the details in natural language.
    * Do not copy/paste.
```
</details>

```
[0] CUSTOMER: I am Norman Bouchard! I have a question about shoes!
[1] AGENT: Hi, what is your question Mr. Bouchard?
[2] CUSTOMER: I am interested in the $94 Tommy Hilfiger boots. I have big feet (size 14). Website says they are unavailable. Are there any in stock?
[3] AGENT: I'd be glad to look into that for you. One moment please.
[4] ACTION search-faq() :: Searching the FAQ pages ...
[5] ACTION search-boots() :: System Action: search boots
[6] AGENT: They do come in a wide variety of sizes, but if the site says out of stock then they are out stock.
[7] CUSTOMER: What is the closest size to 14 that you have in stock?
[8] AGENT: I apologize for the inconvenience but would encourage you to check again tomorrow because they are usually refilled at the end of the month.
[9] ACTION select-faq(boots_other_3) :: FAQ answer related to boots (other3) was selected.
[10] CUSTOMER: Ok, I guess I, the great and illustrious NORMAN BOUCHARD, will do that. I thank you for your help.
[11] AGENT: The site will let you know which sizes are in stock. Is there anything else?
[12] CUSTOMER: No thanks. Have a good day!
```

## L16 · subflow `refund_initiate`

Required steps in order: pull-up-account -> validate-purchase -> record-reason -> enter-details -> offer-refund

<details><summary>Guideline section</summary>

```
### SECTION product_defect/refund_initiate :: Product Defect / Initiate Refund
Flow: Product Defect (refunds and returns)
Required action sequence: pull-up-account -> validate-purchase -> record-reason -> enter-details -> offer-refund
Actions this section lists: pull-up-account, validate-purchase, record-reason, enter-details, offer-refund
- Start by asking for the refund reason.  Then, to complete the refund, perform the following actions
- As always, wrap up by nicely asking if the customer needs any further assistance.
Step 1 [Pull up Account -> pull-up-account]: All chats in this flow start by asking the customer for their full name or Account ID using [Pull up Account].  This will pull up their account in the background with the right information related to this user.
Step 2 [Validate Purchase -> validate-purchase]: To confirm that their purchase is valid with [Validate Purchase]:
    * Username - occasionally, the customer may not remember their username.  In this case, use the Recover Username subflow in the Account Access flow
    * Email Address
    * Order ID - last item, to be consistent with verify identity
Step 3 [Record Reason -> record-reason]: Refund method in [Record Reason] - valid options are
    * Gift card - they want a prepaid gift card, also ask for their address so you know where to mail it.  Enter this value in the next step.
    * Add value - to add value to their account.
    * Paper check - also ask for their address so you know where to mail the check.  Enter this address in the next step.
    * Credit card - direct refund to their credit card, assume a credit card is already on file.  To find it, you will need the account ID, which is entered in the next step.
Step 4 [Enter Details -> enter-details]: Add in additional information using [Enter Details]
    * If the customer chose gift card or paper check then enter the full address
    * If the customer chose add value or credit card then enter the account ID
Step 5 [Offer Refund -> offer-refund]: Dollar amount - enter this value into the details form (without the dollar sign)
    * Then click [Offer Refund]
    * If the customer does not know, the default amount is $50
```
</details>

```
[0] AGENT: Hello. How can i help you today?
[1] CUSTOMER: I would like a refund because I have changed my mind on the item I purchased
[2] AGENT: Okay one moment
[3] CUSTOMER: ok
[4] AGENT: The reason for requesting a refund is you changed your mind correct?
[5] CUSTOMER: correct
[6] AGENT: Can I get your full name please?
[7] CUSTOMER: im trying to get the refund before the item ships
[8] CUSTOMER: Albert Sanders
[9] ACTION pull-up-account(albert sanders) :: Account has been pulled up for Albert Sanders.
[10] AGENT: can i get your username, email address, and order ID please?
[11] CUSTOMER: Username: albertsanders121
[12] CUSTOMER: Order ID: 6750850510
[13] CUSTOMER: Email Address: albertsanders121@email.com
[14] ACTION validate-purchase(albertsanders121, albertsanders121@email.com, 6750850510) :: Purchase validation in progress ...
[15] AGENT: what refund method are you requesting?
[16] CUSTOMER: the card that is on the account
[17] AGENT: Okay in that case I will need your account ID as well
[18] CUSTOMER: Account ID: AYBLQUG0IL
[19] ACTION enter-details(ayblqug0il) :: Details of AYBLQUG0IL have been entered.
[20] AGENT: How much was the order for?
[21] CUSTOMER: $59
[22] ACTION offer-refund(59) :: A refund has been made for the amount of $59.
[23] AGENT: Okay I have issued you a refund
[24] CUSTOMER: Thank you
[25] AGENT: Is there anything else I can do for you today?
[26] CUSTOMER: That is everything
```

## L17 · subflow `membership`

Required steps in order: search-faq -> search-membership -> select-faq

<details><summary>Guideline section</summary>

```
### SECTION storewide_query/membership :: Storewide Query / Membership FAQ
Flow: Storewide Query (FAQ questions about pricing, timing, membership or features)
Required action sequence: search-faq -> search-membership -> select-faq
Actions this section lists: search-faq, search-membership, select-faq
- The main effort is in figuring out which question the customer is asking:
- What are all the membership levels?, How does a customer qualify for premium membership?, What are some of the benefits of membership?, How long does membership last?
Step 1 [Search FAQ -> search-faq]: When you realize that the customer is asking something that can be found in the FAQ, click the [Search FAQ] button
    * This will swap out for a different view that has FAQ content
    * If you made an error, just click [Hide FAQ] to switch back
Step 2 [Membership -> search-membership]: Decide which kind of question the customer is asking about:
    * Possible options are Pricing, Timing, Membership and Policies
    * Click the membership toggle switch
    * This will record an action, so try to get this decision correct.
    * The flow diagram allows you to see all the questions at once.
Step 3 [Select Answer -> select-faq]: Read through the list of 4 options
    * Click [Select Answer] for the correct answer to the customer’s question
    * Remember the category for the survey later
Step 4 [N/A -> no action (talk to the customer)]: The automated system response does not include all the information, so make sure to explain the details in natural language.
    * You should not copy/paste
```
</details>

```
[0] AGENT: Hi, there.  How can I help you?
[1] CUSTOMER: Can you explain the membership levels.  I'm thinking of buying something.
[2] AGENT: Absolutely.
[3] CUSTOMER: thanks
[4] ACTION search-membership() :: System Action: search membership
[5] ACTION search-faq() :: Searching the FAQ pages ...
[6] ACTION select-faq(membership_1) :: FAQ answer related to membership (question1) was selected.
[7] AGENT: We have three levels:  Bronze, Silver, and Gold.
[8] ACTION select-faq(membership_3) :: FAQ answer related to membership (question3) was selected.
[9] AGENT: All levels are invited to our holiday extravaganza with open bar and free flights from anywhere in the US.
[10] CUSTOMER: wow nice
[11] AGENT: Bronze members save on shipping fees and promo codes.
[12] AGENT: Silver members do, too, and they can have agents make purchases on their behalf and cancel orders at any time.
[13] AGENT: Gold members enjoy all of the aforementioned perks, and also get unlimited refunds and will always be given the benefit of the doubt in any transaction.
[14] CUSTOMER: Great.  That was very informative.  This will help me with my shopping decisions.  Thank you
[15] AGENT: You are very welcome.  Please reach out again if you have any more questiions.
[16] CUSTOMER: I will.  Thank you.  have a nice day
[17] AGENT: You, too.  take care.
```

## L18 · subflow `recover_username`

Required steps in order: pull-up-account -> verify-identity

<details><summary>Guideline section</summary>

```
### SECTION account_access/recover_username :: Account Access / Recover Username
Flow: Account Access (username, password, and two-factor authentication)
Required action sequence: pull-up-account -> verify-identity
Actions this section lists: pull-up-account, verify-identity
- To get their username, you must
- That’s it. This flow is very short and often occurs in conjunction with other flows.
Step 1 [Pull up Account -> pull-up-account]: Ask the customer for their Full name or Account ID with [Pull up Account].   This loads information in the background related to this user.
Step 2 [Verify Identity -> verify-identity]: Ask the customer for 3 out of 4 items below and use the [Verify Identity] button
    * Full name - first and last
    * Zip Code
    * Phone number
    * Email Address
Step 3 [N/A -> no action (talk to the customer)]: You make up their username with the first letter of their first name, their last name with a 1
    * For example: John Smith → jsmith1
    * For example: Wendy Chesterfield → wchesterfield1
    * If you are here as part of [Validate Purchase] action or some external flow assume this new username is correct even if the system says it is not valid, and just continue forward with the conversation
```
</details>

```
[0] AGENT: Hello, how may I help you today?
[1] CUSTOMER: I forgot my username like a moron.  Can you help me?
[2] AGENT: Don't be so hard on yourself, people forget their username all the time. I would be happy to help you recover your username.
[3] AGENT: May I have your full name and account ID?
[4] CUSTOMER: Thanks, Rodriguez Domingo, but I don't have an ID?
[5] AGENT: That's okay.
[6] ACTION pull-up-account(rodriguez domingo) :: Account has been pulled up for Rodriquez Domingo.
[7] AGENT: Alright, Mr. Domingo. I need two of the following: email, zip code, or phone number.
[8] CUSTOMER: rodriguezdomingo035@email.com
[9] CUSTOMER: 68466
[10] ACTION verify-identity(rodriguez domingo, 68466, rodriguezdomingo035@email.com) :: Identity verification in progess ...
[11] AGENT: Alright, your username is rdomingo1.
[12] CUSTOMER: Thank you!
[13] AGENT: No problem! Will that be all?
[14] CUSTOMER: Yes, that is all.
[15] AGENT: Have a great day!
```

## L19 · subflow `return_color`

Required steps in order: pull-up-account -> validate-purchase -> membership -> enter-details -> update-order

<details><summary>Guideline section</summary>

```
### SECTION product_defect/return_color :: Product Defect / Return Due to Color
Flow: Product Defect (refunds and returns)
Required action sequence: pull-up-account -> validate-purchase -> membership -> enter-details -> update-order
Actions this section lists: pull-up-account, validate-purchase, membership, enter-details, update-order
- In all three cases for return, follow the same set of actions:
- As usual, end by asking if the customer needs any other assistance.
Step 1 [Pull up Account -> pull-up-account]: Get Full Name or Account ID for [Pull up Account]
Step 2 [Validate Purchase -> validate-purchase]: Confirm that their purchase is valid with [Validate Purchase]
    * Username - occasionally, the customer may not remember their username.  In this case, use the Recover Username subflow in the Account Access flow
    * Email Address
    * Order ID
Step 3 [Membership Privileges -> membership]: Confirm their order can be returned, by checking their membership level.
    * Gold members: > Gold members get unlimited returns
    * Silver members: > Ask for the purchase date, return possible within the last 6 months <or> Ask if they have a receipt, get to return if user has receipt <or> Ask if in original packaging, get to return if in original packaging
    * Bronze members: > Ask for the purchase date, return possible within the last 90 days <or> Ask if they have a receipt, get to return if user has receipt <or> Ask if in original packaging, get to return if in original packaging
    * Guest members: > Ask for the purchase date, return possible within the last 30 days <or> Ask if they have a receipt, get to return if user has receipt
    * Enter the member level and then click the [Membership Privileges] option
Step 4 [End Conversation -> no action (talk to the customer)]: Communication
    * If the customer can return, tell them the good news and go to the next step
    * If the customer cannot return, apologize and explain the problem. Then [End Conversation]
Step 5 [Enter Details -> enter-details]: Since the customer will print out a shipping label for the return, you need their full address.  You can give this explanation if the customer asks why you need the address.
    * Street Number and Street Name
    * City, State, Zip Code
    * Fill this as one line into [Enter Details]
Step 6 [Update Order -> update-order]: Ask the customer how they would like to process their return:
    * Options include: 'By Mail', 'In Store', or 'Drop off Center'
    * Fill in the form with one of these three values and submit to [Update Order]
```
</details>

```
[0] AGENT: Thank you for being an AcmeBrands shopper! How may I help you?
[1] CUSTOMER: I want to return an item because it came in the wrong color.
[2] AGENT: I can help you with that. May I have your full name?
[3] CUSTOMER: Rodriguez Domingo
[4] ACTION pull-up-account(rodriguez domingo) :: Account has been pulled up for Rodriguez Domingo.
[5] AGENT: May I also have your username, email address, and order ID to validate your purchase?
[6] CUSTOMER:  rd090959 rd090959@email.com
[7] CUSTOMER: 2762764761
[8] ACTION validate-purchase(rd090959, rd090959@email.com, 2762764761) :: Purchase validation in progress ...
[9] AGENT: Thank you. What membership do you have?
[10] CUSTOMER: silver
[11] ACTION membership(silver) :: Membership level of silver has been noted.
[12] AGENT: When did you make the purchase?
[13] CUSTOMER: 2019-10-16
[14] AGENT: You're in luck! You can return your item. May I have your full address?
[15] CUSTOMER: 4852 Circle Drive  Jacksonville, TX 1680
[16] ACTION enter-details(4852 circle drive jacksonville, tx 1680) :: Details of 4852 Circle Drive Jacksonville, TX 1680 have been entered.
[17] AGENT: How would you like to process your return? You can send it via mail, take it to a store or to a drop off center.
[18] CUSTOMER: by mail is fine
[19] ACTION update-order(by mail) :: Order has been updated with by mail.
[20] AGENT: You will receive your shipping label shortly for your return. Is there anything else I can help you with?
[21] CUSTOMER: thanks for the help that was everything, have a good day
[22] AGENT: You too!
```

## L20 · subflow `shirt`

Required steps in order: search-faq -> search-shirt -> select-faq

<details><summary>Guideline section</summary>

```
### SECTION single_item_query/shirt :: Single-Item Query / Shirt FAQ
Flow: Single-Item Query (FAQ questions about jeans, boots, shirt or sweater)
Required action sequence: search-faq -> search-shirt -> select-faq
Actions this section lists: search-faq, search-shirt, select-faq
- The main effort is in figuring out which question the customer is asking:
- remove a stain from the shirt, how to wash the shirt, how long is the arm length, how wide is the collar, does this shirt shrink, has any small/medium/large in stock, buttons in brown or black, what material the shirt is made of
Step 1 [Search FAQ -> search-faq]: When you realize that the customer is asking something that can be found in the FAQ, click the [Search FAQ] button
    * This will swap out for a different view that has FAQ content
    * If you made an error, just click [Hide FAQ] to switch back
Step 2 [Shirt -> search-shirt]: Decide which article of clothing the customer is asking about:
    * Possible options are Jeans, Shirt, Boots and Jacket
    * Click the shirt toggle switch
    * This will record an action, so try to get this decision correct
    * The flow diagram allows you to see all the questions at once.
Step 3 [Select Answer -> select-faq]: Read through the list of 8 options
    * Select the correct answer for the customer’s question with [Select Answer]
    * Remember the question your selected for the survey later
Step 4 [N/A -> no action (talk to the customer)]: The system created response does not include all the information, so make sure to explain the details in natural language.
    * Do not copy/paste.
```
</details>

```
[0] CUSTOMER: Hi, I wanted to know more about one of your products.
[1] AGENT: which product might that be
[2] CUSTOMER: The tommy hilfiger shirt that costs $69.
[3] CUSTOMER: I want to know how to remove a bad stain from the shirt.
[4] CUSTOMER: I accidentally spilled some pasta sauce on mine. Whoops!
[5] AGENT: i can assist with that today, the information on the shirt that is, may i have your name?
[6] CUSTOMER: Sanya Afzal
[7] AGENT: ok sanya let me look that up for you
[8] CUSTOMER: Thank you
[9] ACTION search-shirt() :: System Action: search shirt
[10] AGENT: alright
[11] AGENT: to remove a fresh stain, simpling clean with cold water
[12] AGENT: if it has dried it will be harder, but possible
[13] AGENT: start soaking the shirt in cold water for half an hour, then scrub the stain with dish liquid, with something like a toothbrush
[14] AGENT: then wash it normally in cold water
[15] ACTION select-faq(shirt_how_1) :: FAQ answer related to shirt (how1) was selected.
[16] CUSTOMER: Oh okay, sounds like I can do that.
[17] CUSTOMER: That's all I needed, thank you!
[18] AGENT: is there anything else you needed assistance with or clarification on today
[19] AGENT: have a good one
```
