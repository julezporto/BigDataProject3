import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.IOException;

// DS503 Project 3, Question 2 (Step 1): Spark-RDDs (Grid Cells of High Relative-Density Index) - Create the Dataset

public class Main {

    public static void main(String[] args) {
        Main fileMaker = new Main();

        // Create the Points dataset
        fileMaker.createPoints();
    }

    int max_x = 10000;
    int max_y = 10000;
    int min = 0;

    // Create set of 2D points with random integer values for x and y coordinates
    public void createPoints() {
        // Save dataset in Points.txt file
        try (BufferedWriter writer = new BufferedWriter(new FileWriter("Points.txt"))) {

            // Create 10 coordinate points -- change to whatever is above 100MB
            for (int i = 1; i <= 10000000; i++) {

                // x coordinate: random int between 0 and 10 -- change to 10,000
                int x = getRandomInteger(min, max_x - 1);

                // y coordinate: random int between 0 and 10 -- change to 10,000
                int y = getRandomInteger(min, max_y - 1);

                // Write point to file: fields separated by commas & each point on new line
                writer.write(x + "," + y);
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

}
