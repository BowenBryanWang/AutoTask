import mysql.connector


class Database:
    def __init__(self, user, password, host, database):
        """
        Initializes a new instance of the Database class.

        Args:
            user (str): The username to connect to the database.
            password (str): The password to connect to the database.
            host (str): The host address of the database.
            database (str): The name of the database to connect to.
        """
        self.cnx = mysql.connector.connect(
            user=user, password=password, host=host, database=database)
        self.cursor = self.cnx.cursor()

    def create_tables(self):
        """
        Creates the Pages and Edges tables in the database.
        """
        self.cursor.execute("""
        CREATE TABLE Pages (
            PageID VARCHAR(255) PRIMARY KEY,
            PageInfo JSON
        )
        """)
        self.cursor.execute("""
        CREATE TABLE Edges (
            EdgeID INT AUTO_INCREMENT PRIMARY KEY,
            SourcePageID VARCHAR(255),
            DestinationPageID VARCHAR(255),
            Action VARCHAR(255),
            FOREIGN KEY (SourcePageID) REFERENCES Pages(PageID),
            FOREIGN KEY (DestinationPageID) REFERENCES Pages(PageID)
        )
        """)

    def insert_page(self, page_id, page_info):
        """
        Inserts a new page into the Pages table.

        Args:
            page_id (str): The ID of the page to insert.
            page_info (str): The JSON string containing the page information.
        """
        add_page = ("INSERT INTO Pages (PageID, PageInfo) VALUES (%s, %s)")
        self.cursor.execute(add_page, (page_id, page_info))

    def insert_edge(self, source_page_id, destination_page_id, action):
        """
        Inserts a new edge into the Edges table.

        Args:
            source_page_id (str): The ID of the source page.
            destination_page_id (str): The ID of the destination page.
            action (str): The action that triggers the edge.
        """
        add_edge = (
            "INSERT INTO Edges (SourcePageID, DestinationPageID, Action) VALUES (%s, %s, %s)")
        self.cursor.execute(
            add_edge, (source_page_id, destination_page_id, action))

    def get_all_pages(self):
        """
        Retrieves all pages from the Pages table.

        Returns:
            A list of tuples representing the pages.
        """
        self.cursor.execute("SELECT * FROM Pages")
        return self.cursor.fetchall()

    def get_all_edges(self):
        """
        Retrieves all edges from the Edges table.

        Returns:
            A list of tuples representing the edges.
        """
        self.cursor.execute("SELECT * FROM Edges")
        return self.cursor.fetchall()

    def commit(self):
        """
        Commits the changes to the database.
        """
        self.cnx.commit()

    def close(self):
        """
        Closes the database connection.
        """
        self.cursor.close()
        self.cnx.close()

    def get_page(self, page_id):
        """
        Retrieves a page from the Pages table.

        Args:
            page_id (str): The ID of the page to retrieve.

        Returns:
            A tuple representing the page.
        """
        query = ("SELECT * FROM Pages WHERE PageID = %s")
        self.cursor.execute(query, (page_id,))
        return self.cursor.fetchone()

    def get_edges_from(self, source_page_id):
        """
        Retrieves all edges that originate from a source page.

        Args:
            source_page_id (str): The ID of the source page.

        Returns:
            A list of tuples representing the edges.
        """
        query = ("SELECT * FROM Edges WHERE SourcePageID = %s")
        self.cursor.execute(query, (source_page_id,))
        return self.cursor.fetchall()

    def get_edges_to(self, destination_page_id):
        """
        Retrieves all edges that lead to a destination page.

        Args:
            destination_page_id (str): The ID of the destination page.

        Returns:
            A list of tuples representing the edges.
        """
        query = ("SELECT * FROM Edges WHERE DestinationPageID = %s")
        self.cursor.execute(query, (destination_page_id,))
        return self.cursor.fetchall()

    def get_destination(self, source_page_id, action):
        """
        Retrieves the destination page ID for a given source page and action.

        Args:
            source_page_id (str): The ID of the source page.
            action (str): The action that triggers the edge.

        Returns:
            The ID of the destination page, or None if no such edge exists.
        """
        query = (
            "SELECT DestinationPageID FROM Edges WHERE SourcePageID = %s AND Action = %s")
        self.cursor.execute(query, (source_page_id, action))
        result = self.cursor.fetchone()
        return result[0] if result else None
