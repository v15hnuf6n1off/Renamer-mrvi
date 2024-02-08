from helper.utils import progress_for_pyrogram, convert
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from helper.database import db
import os
import humanize
from PIL import Image
import time

@Client.on_callback_query(filters.regex('cancel'))
async def cancel(bot, update):
    try:
        await update.message.delete()
    except:
        return

@Client.on_callback_query(filters.regex('rename'))
async def rename(bot, update):
    user_id = update.message.chat.id
    date = update.message.date

    # Delete the original callback query message
    await update.message.delete()

    # Reply to the user, asking for the new filename
    await update.message.reply_text("__𝙿𝚕𝚎𝚊𝚜𝚎 𝙴𝚗𝚝𝚎𝚛 The 𝙽𝚎𝚠 𝙵𝚒𝚕𝚎𝙽𝚊𝚖𝚎...__",
                                     reply_to_message_id=update.message.reply_to_message.id,
                                     reply_markup=ForceReply(True))

# Add a new message handler for the user's response with the new filename
@Client.on_message(filters.reply & filters.force_reply)
async def handle_rename_response(bot, update):
    # Assuming the replied message is the user's response
    new_name = update.message.text.strip()

    # Add code here to edit metadata based on the new filename (e.g., using hachoir)
    # For simplicity, let's assume you have a function 'edit_metadata' to handle metadata editing
    edited_metadata = edit_metadata(update.message.reply_to_message, new_name)

    # Reply to the user that metadata has been edited
    await update.message.reply_text("Metadata edited successfully!")

# Define a function to edit metadata (replace this with your actual logic)
def edit_metadata(original_message, new_name):
    # Add your metadata editing logic here, using hachoir or any other library
    # Example: You can extract and update metadata like title, artist, etc.

    # For demonstration purposes, let's assume updating the title with the new filename
    metadata = extractMetadata(createParser(original_message.file_path))
    metadata.set('title', new_name)
    edited_metadata = metadata.exportPlaintext()

    # Return the edited metadata (this is just a placeholder)
    return f"Edited Metadata: {edited_metadata}"

@Client.on_callback_query(filters.regex("upload"))
async def doc(bot, update):
    type = update.data.split("_")[1]
    new_name = update.message.text
    new_filename = new_name.split(":-")[1]
    file_path = f"downloads/{new_filename}"
    file = update.message.reply_to_message
    ms = await update.message.edit("𝚃𝚁𝚈𝙸𝙽𝙶 𝚃𝙾 𝙳𝙾𝚆𝙽𝙻𝙾𝙰𝙳...")
    c_time = time.time()
    try:
        path = await bot.download_media(message=file, progress=progress_for_pyrogram,
                                        progress_args=("𝚃𝚁𝚈𝙸𝙽𝙶 𝚃𝙾 𝙳𝙾𝚆𝙽𝙻𝙾𝙰𝙳....", ms, c_time))
    except Exception as e:
        await ms.edit(e)
        return
    splitpath = path.split("/downloads/")
    dow_file_name = splitpath[1]
    old_file_name = f"downloads/{dow_file_name}"
    os.rename(old_file_name, file_path)
    duration = 0
    try:
        metadata = extractMetadata(createParser(file_path))
        if metadata.has("duration"):
            duration = metadata.get('duration').seconds
    except:
        pass
    user_id = int(update.message.chat.id)
    ph_path = None
    media = getattr(file, file.media.value)
    c_caption = await db.get_caption(update.message.chat.id)
    c_thumb = await db.get_thumbnail(update.message.chat.id)
    if c_caption:
        try:
            caption = c_caption.format(filename=new_filename, filesize=humanize.naturalsize(media.file_size),
                                       duration=convert(duration))
        except Exception as e:
            await ms.edit(text=f"Your caption Error unexpected keyword ●> ({e})")
            return
    else:
        caption = f"**{new_filename}**"
    if (media.thumbs or c_thumb):
        if c_thumb:
            ph_path = await bot.download_media(c_thumb)
        else:
            ph_path = await bot.download_media(media.thumbs[0].file_id)
        Image.open(ph_path).convert("RGB").save(ph_path)
        img = Image.open(ph_path)
        img.resize((320, 320))
        img.save(ph_path, "JPEG")
    await ms.edit("𝚃𝚁𝚈𝙸𝙽𝙶 𝚃𝙾 𝚄𝙿𝙻𝙾𝙰𝙳𝙸𝙽𝙶....")
    c_time = time.time()
    try:
        if type == "document":
            await bot.send_document(
                update.message.chat.id,
                document=file_path,
                thumb=ph_path,
                caption=caption,
                progress=progress_for_pyrogram,
                progress_args=("𝚃𝚁𝚈𝙸𝙽𝙶 𝚃𝙾 𝚄𝙿𝙻𝙾𝙰𝙳𝙸𝙽𝙶....", ms, c_time))
        elif type == "video":
            await bot.send_video(
                update.message.chat.id,
                video=file_path,
                caption=caption,
                thumb=ph_path,
                duration=duration,
                progress=progress_for_pyrogram,
                progress_args=("𝚃𝚁𝚈𝙸𝙽𝙶 𝚃𝙾 𝚄𝙿𝙻𝙾𝙰𝙳𝙸𝙽𝙶....", ms, c_time))
        elif type == "audio":
            await bot.send_audio(
                update.message.chat.id,
                audio=file_path,
                caption=caption,
                thumb=ph_path,
                duration=duration,
                progress=progress_for_pyrogram,
                progress_args=("𝚃𝚁𝚈𝙸𝙽𝙶 𝚃𝙾 𝚄𝙿𝙻𝙾𝙰𝙳𝙸𝙽𝙶....", ms, c_time))
    except Exception as e:
        await ms.edit(f" Erro {e}")
        os.remove(file_path)
        if ph_path:
            os.remove(ph_path)
        return
    await ms.delete()
    os.remove(file_path)
    if ph_path:
        os.remove(ph_path)
