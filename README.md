| ![clockout](https://github.com/user-attachments/assets/d246170f-61a1-48f0-bc7b-92d4b0a748c8) | ClockOut is a simple GTK3-based GUI tool for Linux distros to schedule system shutdowns. Available in English & German. <br/><br/> |
| --- | --- |


Ever downloaded a large game or copied big chunks of data and you didn't want to let your PC run the whole night when the task would be complete in 3 hours? <br/><br/>
ClockOut lets you easily schedule a shutdown without needing a terminal, so your PC automatically powers off when it's no longer needed.




<br/><br/>
| either enter your desired time (24hr format)... | ...a duration in minutes... |  ...or even in hours (HH:MM) | 
| --- | --- | --- |
|![](https://github.com/user-attachments/assets/47c84e4c-61f0-4f35-a91a-4483758e4ede)|![](https://github.com/user-attachments/assets/b332ea48-9b80-4acc-86f6-63f9dfc6c698)|![](https://github.com/user-attachments/assets/35f286eb-f573-457a-9442-88b3c89ba7ee)|
<br/><br/>

| adapts to dark... | ...and light themes|
| --- | --- |
| ![](https://github.com/user-attachments/assets/47c84e4c-61f0-4f35-a91a-4483758e4ede) | ![](https://github.com/user-attachments/assets/750c0859-d10c-4e23-862b-7f17c865425e)
<br/><br/>

|   | The progress bar visually indicates the approaching shutdown at one glance |   |
| --- | :---: | --- |
|____________________|![](https://github.com/user-attachments/assets/a8d801fd-7d38-4db5-af96-8f00d8f13252)|____________________|
<br/><br/>

| you can schedule a shutdown for the next day... | ...or basically any future date and time |
| --- | --- |
| ![Bildschirmfoto vom 2025-02-07 21-28-01](https://github.com/user-attachments/assets/1cb420bd-b302-4c18-a416-cee1f953a2a4)| ![](https://github.com/user-attachments/assets/911cf250-fb7c-42d4-8872-490dcb63b12e)|
<br/><br/>

|   | You think the GUI is bloated? Try out "Mini ClockOut" which has been reduced to the essential GUI elements while maintaining the same functionality |   |
| --- | :---: | --- |
|____________________|![](https://github.com/user-attachments/assets/69f424f0-0648-4fb6-a27e-2d46702f1421)|____________________|
<br/><br/>


| available in three versions: <br/> English (US), German and English (EU) |
| :---: |
|![](https://github.com/user-attachments/assets/a361527f-4a5b-48ad-a51b-de587a938914)|
<br/><br/>

**Installation:**
<br/><br/>
✅ Simply download your desired version (normal or mini version of your preffered language variant) and extract the archive to your home directory.<br/><br/>
✅ Execute the *install.sh* file found within the *ClockOut* folder to add *ClockOut* to your app menu -it can then be found under "utilities".<br/>❗*Note: when you execute *install.sh* without using the terminal (`sh install.sh`), you do not receive a confirmation that anything has happened, but the app will be installed instantly.* <br/><br/>
✅ launch *ClockOut* from your app menu and happy scheduling!
<br/>
<br/>
**Hint:**
<br/>
To cancel a scheduled shutdown, either close the app or overwrite the scheduled shutdown with a new one.
<br/>Alternatively, when you enter an invalid format into any of the text boxes, scheduled shutdowns also get cancelled.
<br/>
<br/>
**How does it work?**
<br/>
Basically, when scheduling a shutdown, the app uses the command "shutdown -h" with a delay based on your time/duration input.
