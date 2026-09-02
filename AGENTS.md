\# LifeLink AI Frontend Redesign Rules



\## Project goal



Redesign and improve the existing LifeLink AI frontend UI/UX and implement the redesign in the existing frontend.



The goal is to make LifeLink AI feel like a professional, real-world healthcare product while preserving the existing product concept, functionality, backend integration, and project architecture.



\## HARD CONSTRAINTS



1\. DO NOT modify the backend unless a frontend requirement absolutely cannot work without a backend change.

2\. DO NOT change the database models.

3\. DO NOT change existing API endpoints.

4\. DO NOT change the existing blood matching logic.

5\. DO NOT change the existing AI/matching concepts.

6\. DO NOT invent new product functionality.

7\. DO NOT add unrelated features.

8\. DO NOT migrate the project to React, Next.js, Vue, or another framework.

9\. DO NOT restructure the entire repository.

10\. Preserve the existing frontend technology: HTML, CSS and JavaScript.

11\. Preserve existing API calls and functionality in script.js.

12\. Preserve service-worker functionality.

13\. Modify frontend JavaScript only when necessary to connect the redesigned UI to the existing functionality.

14\. Do not remove working functionality just because the UI is being redesigned.



\## Existing frontend



The frontend is located in:



frontend/



Current main files include:



\- index.html

\- style.css

\- script.js

\- service-worker.js

\- icon.png



\## Existing LifeLink functionality



Donor functionality includes:



\- Donor registration

\- Donor login

\- Blood group

\- City

\- Phone

\- Password

\- Donor availability

\- Donor GPS location

\- Blood-request matching

\- Donor notifications

\- Accept request

\- Reject request



Hospital functionality includes:



\- Hospital creation/registration

\- Hospital location

\- Create blood request

\- Blood group selection

\- Units required

\- Request type

\- City

\- View hospital blood requests

\- View donor responses



Matching includes:



\- Blood-group compatibility

\- Location/radius filtering

\- Donor availability

\- Match scoring/ranking

\- Donor notifications

\- Donor accept/reject response



\## UX direction



There are two user experiences under one LifeLink brand.



\### Donor



Primary device: MOBILE.



Donor UI should be:



\- Mobile-first

\- Simple

\- Fast

\- Easy to use with one hand

\- Action-oriented

\- Clear about blood group

\- Clear about emergency priority

\- Clear about distance

\- Clear about request status

\- Clear about accept/reject actions



Donor navigation should conceptually contain:



\- Home

\- Requests

\- Notifications

\- Profile

\- Settings



\### Hospital



Primary device: DESKTOP.



Hospital UI should be:



\- Desktop-first

\- Professional

\- Information-dense but clean

\- Dashboard-oriented

\- Easy to manage blood requests

\- Easy to view donor responses

\- Clear about request status



Hospital navigation should conceptually contain:



\- Dashboard/Home

\- Blood Requests

\- Notifications

\- Profile

\- Settings



\## Important distinction



Do not add new business functionality.



UI/UX improvements are allowed, including:



\- Better layouts

\- Better navigation

\- Better forms

\- Better typography

\- Better spacing

\- Better cards

\- Status badges

\- Loading states

\- Empty states

\- Error states

\- Success feedback

\- Confirmation UI

\- Responsive behavior

\- Accessibility improvements

\- Better visual hierarchy

\- Better mobile interaction

\- Better desktop dashboard organization



These improvements must represent existing functionality, not create new functionality.



\## Authentication



Separate Donor and Hospital authentication screens may be designed as part of the UX.



However, the current backend does not provide complete hospital authentication support.



Do not fake hospital authentication using frontend-only logic.



If backend changes are required for hospital authentication, stop and clearly identify the backend dependency instead of modifying the backend automatically.



\## Design direction



LifeLink should feel:



\- Professional

\- Trustworthy

\- Modern

\- Healthcare-focused

\- Accessible

\- Calm

\- Fast during emergencies



Avoid:



\- Excessive gradients

\- Neon colors

\- Excessive glassmorphism

\- Overly futuristic AI visuals

\- Unnecessary animations

\- Generic template-looking dashboards



Use a consistent LifeLink design system across donor and hospital experiences.



\## Before coding



First inspect the existing frontend and identify:



1\. Existing HTML structure

2\. Existing CSS

3\. Existing JavaScript functions

4\. Existing API calls

5\. Existing DOM IDs used by JavaScript

6\. Existing service-worker behavior



Do not start by deleting the existing implementation.



Create a safe, incremental redesign.



\## Development approach



Implement the redesign incrementally:



1\. Common landing / role selection

2\. Donor authentication UI

3\. Donor mobile home

4\. Donor requests

5\. Donor notifications

6\. Donor profile/settings

7\. Hospital authentication UI

8\. Hospital desktop dashboard

9\. Hospital blood requests

10\. Hospital donor responses

11\. Hospital notifications

12\. Hospital profile/settings

13\. Responsive polish

14\. Accessibility

15\. Final testing



After each major change, verify that existing API functionality still works.



\## Git



Work only on the frontend-redesign branch.



Do not commit directly to master.



Before making major changes:



\- Check git status

\- Preserve the current working version

\- Make small, meaningful commits

