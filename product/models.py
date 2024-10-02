from io import BytesIO
from math import floor

from django.db import models
from PIL import Image
from django.core.files import File
from django.contrib.auth.models import User


class Category(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField()

    class Meta:
        verbose_name_plural = 'Катергории'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    mog = models.CharField(max_length=255, default='')
    slug = models.SlugField(allow_unicode=True)
    description = models.TextField(blank=True, null=True)
    price = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='uploads/', blank=True, null=True)
    thumbnail = models.ImageField(upload_to='uploads/', blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Товары'
        ordering = ('-created_at',)

    def __str__(self):
        return self.name

    def get_display_price(self):
        return self.price

    def get_thumbnail(self):
        if self.thumbnail:
            return self.thumbnail.url
        else:
            if self.image:
                self.thumbnail = self.make_thumbnail(self.image)
                self.save()

                return self.thumbnail.url
            else:
                return '/media/placeholder.jpeg'

    def make_thumbnail(self, image, size=150):
        img = Image.open(image)
        img.convert('RGB')

        thumb_io = BytesIO()
        if img.mode in ("RGBA", "P"): img = img.convert("RGB")
        width, height = img.size
        print(width, height)
        if width == height:
            img.thumbnail((size, size), Image.ANTIALIAS)

        elif height > width:
            ratio = size / float(height)
            new_height = size
            new_width = ratio * width
            img = img.resize((int(floor(new_width)), int(floor(new_height))), Image.ANTIALIAS)
            print(new_width, new_height)
        elif width > height:
            ratio = size / float(width)
            new_height = ratio * height
            new_width = size
            img = img.resize((int(floor(new_width)), int(floor(new_height))), Image.ANTIALIAS)
            print(new_width, new_height)
        if img.mode in ("RGBA", "P"): img = img.convert("RGB")
        new_image = Image.new(img.mode,(img.size[0]+((size-img.size[0]) if img.size[0]<size else 0),
                                        img.size[1]+((size-img.size[1]) if img.size[1]<size else 0)), 'white')
        new_image.paste(img, (int(new_image.size[0]/2-img.size[0]/2), int(new_image.size[1]/2-img.size[1]/2)))
        new_image.save(thumb_io, 'JPEG', quality=85)
        print(new_image.size)
        thumbnail = File(thumb_io, name=image.name)

        return thumbnail

    def get_rating(self):
        reviews_total = 0

        for review in self.reviews.all():
            reviews_total += review.rating

        if reviews_total > 0:
            return reviews_total / self.reviews.count()

        return 0


class ProductItem(models.Model):
    product_item = models.ForeignKey(Product, related_name='product_item', on_delete=models.CASCADE)


class Review(models.Model):
    product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE)
    rating = models.IntegerField(default=3)
    content = models.TextField()
    created_by = models.ForeignKey(User, related_name='reviews', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
