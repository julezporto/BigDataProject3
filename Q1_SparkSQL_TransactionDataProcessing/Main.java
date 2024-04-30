import java.io.*;

// DS503 Project 1, Question 1: Creating Datasets

public class Main {

    public static void main(String[] args) {
        Main fileMaker = new Main();

        // Create a Customers dataset
        fileMaker.createCustomers();

        // Create a Transactions dataset
        fileMaker.createTransactions();
    }

    // Create 50,000 customers with ID, Name, Age, Gender, Country Code, and Salary
    public void createCustomers() {
        // Save dataset in Customers.txt file
        try (BufferedWriter writer = new BufferedWriter(new FileWriter("Customers1.txt"))) {

            // Create 50,000 customers
            for (int i = 1; i <= 50000; i++) {

                // ID: unique sequential number (integer) from 1 to 50,000
                int id = i;

                // Name: random sequence of characters of length between 10 and 20 (no commas)
                String name = getRandomString(10, 20);

                // Age: random number (integer) between 10 and 70
                int age = getRandomInteger(10, 70);

                // Gender: string that is either “male” or “female”
                String gender = getRandomGender();

                // CountryCode: random number (integer) between 1 and 10
                int countryCode = getRandomInteger(1, 10);

                // Salary: random number (float) between 100 and 10000
                float salary = getRandomFloat(100, 10000);

                // Write customer to file: fields separated by commas & each customer on new line
                writer.write(id + "," + name + "," + age + "," + gender + "," + countryCode + "," + salary);
                writer.newLine();

            }

        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    // Create 5,000,000 transactions with Transaction ID, Customer ID, Total, Number Items, and Description
    public void createTransactions() {
        // Save dataset in Transactions.txt file
        try (BufferedWriter writer = new BufferedWriter(new FileWriter("Transactions1.txt"))) {

            // Create 5,000,000 transactions
            for (int i = 1; i <= 5000000; i++) {

                // TransID: unique sequential number (integer) from 1 to 5,000,000
                int transId = i;

                // CustID: References one of the customer IDs, i.e., from 1 to 50,000
                int custId = getRandomInteger(1, 50000);

                // TransTotal: random number (float) between 10 and 1000
                float transTotal = getRandomFloat(10, 1000);

                // TransNumItems: random number (integer) between 1 and 10
                int transNumItems = getRandomInteger(1, 10);

                // TransDesc: random text of characters of length between 20 and 50 (no commas)
                String transDesc = getRandomString(20, 50);

                // Writing transactions to file: fields separated by commas & each transaction on new line
                writer.write(transId + "," + custId + "," + transTotal + "," + transNumItems + "," + transDesc);
                writer.newLine();

            }

        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    // Get a random integer
    private int getRandomInteger(int minNum, int maxNum) {
        // Create and return a random integer between min number and max number
        return (int) (Math.random() * (maxNum - minNum + 1)) + minNum;
    }

    // Get a random float
    private float getRandomFloat(float minNum, float maxNum) {
        // Create and return a random float between min number and max number
        return (float) (Math.random() * (maxNum - minNum)) + minNum;
    }

    // Get a random string without commas
    private String getRandomString(int minStringLength, int maxStringLength) {
        StringBuilder stringBuilder = new StringBuilder();

        // Get random string length between min and max string length
        int length = getRandomInteger(minStringLength, maxStringLength);

        // Make sure no commas are included in string
        String characters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";

        // Create the random string
        for (int i = 0; i < length; i++) {
            int index = getRandomInteger(0, characters.length() - 1);
            stringBuilder.append(characters.charAt(index));
        }

        // Return the random string
        return stringBuilder.toString();
    }

    // Get a random gender
    private String getRandomGender() {
        // Gender options: male or female
        String[] genders = {"male", "female"};

        // Return either male or female at random
        return genders[getRandomInteger(0, 1)];
    }
}
