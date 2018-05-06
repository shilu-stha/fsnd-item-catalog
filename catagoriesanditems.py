from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base, Item, Category, User

engine = create_engine('sqlite:///bigbazar.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

user1 = User(name="Test User", email="test@udacity.com",
             picture='https://testinsane.com/img/custom/Services/UX%20Testing_icons.png')


category1 = Category(name = "Soccer", description = "This is Soccer Category.It is a long established fact that a reader will be distracted by the readable content of a page when looking at its layout. The point of using Lorem Ipsum is that it has a more-or-less normal distribution of letters, as opposed to using 'Content here, content here', making it look like readable English.")
session.add(category1)
session.commit()

# Item for Soccer
item1 = Item(name="Soccer Ball", description="This is ball", price="$0.50", category=category1, user_id = 1)
session.add(item1)
session.commit()

item2 = Item(name="Shin Guard", description="This is shin guard", price="$2.50", category=category1, user_id = 1)
session.add(item2)
session.commit()

item3 = Item(name="Soccer Shoes", description="This is ball", price="$13.45", category=category1, user_id = 1)
session.add(item3)
session.commit()

category2 = Category(name = "Basketball", description = "This is Basketball Category. It is a long established fact that a reader will be distracted by the readable content of a page when looking at its layout. The point of using Lorem Ipsum is that it has a more-or-less normal distribution of letters, as opposed to using 'Content here, content here', making it look like readable English.")
session.add(category2)
session.commit()

# Item for Basketball
item1 = Item(name="Basketballs", description="This is ball", price="$1.50", category=category2, user_id = 1)
session.add(item1)
session.commit()

item2 = Item(name="Hoops", description="This is ball", price="$23.50", category=category2, user_id = 1)
session.add(item2)
session.commit()

item3 = Item(name="Sleeves", description="This is ball", price="$1.50", category=category2, user_id = 1)
session.add(item3)
session.commit()

category3 = Category(name = "Baseball", description= "This is Baseball Category. It is a long established fact that a reader will be distracted by the readable content of a page when looking at its layout. The point of using Lorem Ipsum is that it has a more-or-less normal distribution of letters, as opposed to using 'Content here, content here', making it look like readable English.")
session.add(category3)
session.commit()

# Item for Baseball

category4 = Category(name = "Frisbee", description = "This is Frisbee Category. It is a long established fact that a reader will be distracted by the readable content of a page when looking at its layout. The point of using Lorem Ipsum is that it has a more-or-less normal distribution of letters, as opposed to using 'Content here, content here', making it look like readable English.")
session.add(category4)
session.commit()

# Item for Frisbee


print "added menu items!"
